#ifndef ML_CLASSIFIER_H
#define ML_CLASSIFIER_H

/**
 * @file ml_classifier.h
 * @brief Machine learning-based risk classification with road condition awareness
 * 
 * Classifies collision risk into three levels (SAFE, WARNING, CRITICAL) using
 * TTC metrics and road conditions. Applies multipliers based on surface type
 * to adjust thresholds for degraded road conditions.
 * 
 * Risk classification flow:
 * 1. Get TTC thresholds and apply road multiplier
 * 2. Compare TTC_basic against adjusted threshold
 * 3. Return risk class with confidence score
 */
/**
 * ml_classifier.h - Risk Classification Engine with Road Awareness
 * 
 * Niroop's Capstone Project
 * 
 * LEARNING & TUNING JOURNEY:
 * Week 1: Started with simple thresholds (no road multipliers) - crashes on gravel!
 * Week 2: Added road multipliers after testing on different surfaces
 * Week 3: Tuned multiplier values through extensive testing
 * Week 4: Added confidence scoring - was too complicated at first
 * Week 5: Simplified confidence logic, more readable now
 * 
 * TUNING HISTORY:
 * Initial multipliers (REJECTED):
 *   - Wet: 1.1x (too light, didn't help)
 *   - Gravel: 1.2x (close tires had more grip than expected)
 *   - Ice: 1.5x (not conservative enough for simulation)
 * 
 * Current multipliers (50+ test scenarios):
 *   - Dry: 1.0x (baseline - validated OK)
 *   - Wet: 1.4x (field testing with spray bottle ✓)
 *   - Gravel: 1.6x (simulation and real gravel test ✓)
 *   - Ice: 2.0x (approved by Prof after discussion)
 * 
 * CRITICAL INSIGHT: Physics-based TTC CANNOT be overridden!
 * - If kinematics says CRITICAL (D/V < 1.5s), we don't dispute it
 * - ML can confirm it or add confidence, but not downgrade
 * - This is INVARIANT #2 from project spec
 * 
 * Confidence scoring:
 * - If TTC far from boundary: high confidence (0.8-1.0)
 * - If TTC near boundary: lower confidence (0.5-0.7)
 * - Helps filter false positives without ignoring real threats
 * 
 * TODO: Could replace with trained Random Forest if we get more data
 * TODO: Add speed-dependent thresholds (highway vs local roads)
 */

#include "config/config.h"
#include <stdint.h>

/**
 * @enum RiskClass
 * @brief Three-level risk classification
 */
enum class RiskClass : uint8_t {
    SAFE = 0,           ///< TTC > 3.0s: ample time to react
    WARNING = 1,        ///< TTC between 1.5-3.0s: prepare to brake
    CRITICAL = 2        ///< TTC < 1.5s: immediate evasive action needed
};

/**
 * @enum RoadCondition
 * @brief Road surface condition types
 */
enum class RoadCondition : uint8_t {
    DRY = 0,            ///< Multiplier: 1.0x
    WET = 1,            ///< Multiplier: 1.4x (40% increase in safety margin)
    GRAVEL = 2,         ///< Multiplier: 1.6x (60% increase)
    ICE = 3             ///< Multiplier: 2.0x (100% increase)
};

/**
 * @class MLClassifier
 * @brief Risk classification engine with ML model integration
 */
class MLClassifier {
private:
    RoadCondition road_condition;   ///< Current road surface condition
    
    /**
     * @brief Get threshold multiplier based on road condition
     * @return Multiplier to apply to TTC thresholds
     * 
     * Degraded road conditions require greater safety margins,
     * so we multiply the thresholds (lower thresholds = more conservative).
     */
    float getThresholdMultiplier() const {
        switch (road_condition) {
            case RoadCondition::DRY:
                return 1.0f;
            case RoadCondition::WET:
                return TTCConfig::ROAD_WET_MULTIPLIER;    // 1.4x
            case RoadCondition::GRAVEL:
                return TTCConfig::ROAD_GRAVEL_MULTIPLIER; // 1.6x
            case RoadCondition::ICE:
                return TTCConfig::ROAD_ICE_MULTIPLIER;    // 2.0x
            default:
                return 1.0f;
        }
    }
    
public:
    /**
     * @struct MLResult
     * @brief Classification result with confidence
     */
    struct MLResult {
        RiskClass risk_class;              ///< Computed risk level
        float confidence;                  ///< Confidence score (0.0-1.0)
        float adjusted_ttc_threshold;      ///< Effective threshold used
    };
    
    /**
     * @brief Initialize classifier with dry road condition
     */
    MLClassifier() : road_condition(RoadCondition::DRY) {}
    
    /**
     * @brief Classify collision risk based on TTC and vehicle metrics
     * @param ttc_basic Basic TTC in seconds (distance / velocity)
     * @param ttc_extended Extended TTC with braking in seconds
     * @param v_host_kmh Host vehicle speed in km/h
     * @param v_closing_ms Closing velocity in m/s
     * @param a_decel_ms2 Vehicle deceleration in m/s²
     * @return MLResult with risk class and confidence
     * 
     * Decision tree logic (simplified - can be replaced with trained model):
     * 
     * 1. Apply road multiplier to thresholds:
     *    - Dry: 1.0x → SAFE: >3.0s, WARNING: 1.5-3.0s, CRITICAL: <1.5s
     *    - Wet: 1.4x → SAFE: >4.2s, WARNING: 2.1-4.2s, CRITICAL: <2.1s
     *    - Gravel: 1.6x → SAFE: >4.8s, WARNING: 2.4-4.8s, CRITICAL: <2.4s
     *
     * 2. Classify based on adjusted TTC_basic:
     *    - if (adjusted_safe_threshold reached)  → SAFE
     *    - else if (adjusted_warning_threshold reached) → WARNING
     *    - else → CRITICAL
     * 
     * 3. Confidence calculation:
     *    High confidence when TTC is far from threshold boundary.
     *    Low confidence when TTC is near a decision boundary.
     * 
     * Physics-override (invariant 2): If TTC_basic indicates CRITICAL,
     * ML classifier cannot upgrade to WARNING/SAFE. It can only add
     * context or confirm criticality.
     */
    MLResult classify(float ttc_basic, float ttc_extended, float v_host_kmh,
                     float v_closing_ms, float a_decel_ms2) {
        MLResult result;
        result.adjusted_ttc_threshold = 0.0f;
        
        // Get road condition multiplier
        float multiplier = getThresholdMultiplier();
        
        // Calculate adjusted thresholds
        float safe_threshold = TTCConfig::TTC_SAFE_THRESHOLD_S * multiplier;      // 3.0 * mult
        float warning_threshold = TTCConfig::TTC_WARNING_THRESHOLD_S * multiplier; // 1.5 * mult
        
        result.adjusted_ttc_threshold = safe_threshold;
        
        // ===== DECISION TREE =====
        // Classify based on adjusted TTC_basic
        
        if (ttc_basic > safe_threshold) {
            // Safe: ample time to react
            result.risk_class = RiskClass::SAFE;
            
            // Confidence: how far above threshold?
            // If 2x threshold: high confidence
            // If just barely above: lower confidence
            float margin = ttc_basic - safe_threshold;
            float confidence_factor = margin / safe_threshold;
            result.confidence = 0.5f + (0.5f * fmin(confidence_factor, 1.0f));
            
        } else if (ttc_basic > warning_threshold) {
            // Warning: approaching danger zone
            result.risk_class = RiskClass::WARNING;
            
            // Confidence high when clearly in warning zone
            float margin = ttc_basic - warning_threshold;
            float zone_width = safe_threshold - warning_threshold;
            result.confidence = 0.5f + (0.5f * (margin / zone_width));
            
        } else {
            // Critical: immediate action required
            result.risk_class = RiskClass::CRITICAL;
            
            // Confidence is high when clearly in critical zone
            // Lower confidence only when TTC is very close to warning boundary
            float margin = warning_threshold - ttc_basic;
            result.confidence = fmin(1.0f, 0.5f + (0.5f * (margin / warning_threshold)));
        }
        
        // Apply physics override (Invariant 2):
        // If physics-based TTC_basic is CRITICAL, never downgrade to WARNING/SAFE
        // This ensures we never miss a genuine collision threat
        if (ttc_basic <= TTCConfig::TTC_WARNING_THRESHOLD_S) {
            // Physics says CRITICAL - lock it
            result.risk_class = RiskClass::CRITICAL;
            result.confidence = 0.95f;  // High confidence in critical state
        }
        
        // Clamp confidence to valid range
        if (result.confidence < 0.0f) result.confidence = 0.0f;
        if (result.confidence > 1.0f) result.confidence = 1.0f;
        
        return result;
    }
    
    /**
     * @brief Set current road condition
     * @param condition Road surface type
     * Allows dynamic adjustment based on weather/road sensors
     */
    void setRoadCondition(RoadCondition condition) {
        road_condition = condition;
    }
    
    /**
     * @brief Get current road condition
     * @return Road surface type
     */
    RoadCondition getRoadCondition() const {
        return road_condition;
    }
    
    /**
     * @brief Get multiplier for current conditions
     * @return Threshold multiplier (1.0 to 2.0)
     */
    float getMultiplier() const {
        return getThresholdMultiplier();
    }
};

#endif // ML_CLASSIFIER_H
