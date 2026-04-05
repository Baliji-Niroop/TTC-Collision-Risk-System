#ifndef TTC_CALCULATOR_H
#define TTC_CALCULATOR_H

/**
 * @file ttc_calculator.h
 * @brief Time-to-Collision calculation engine
 * 
 * Maintains short-term history of distance measurements to compute:
 * 1. Closing velocity (how fast gap is closing)
 * 2. TTC Basic (D / V_closing)
 * 3. TTC Extended (includes deceleration: (-V + sqrt(V² + 2*a*D)) / a)
 * 
 * Extended formula accounts for both objects braking, providing more 
 * realistic prediction when collision avoidance is possible.
 */
/**
 * ttc_calculator.h - Time-to-Collision Computation Engine
 * 
 * Niroop's Capstone Project
 * 
 * LEARNING JOURNEY:
 * Week 1: First tried simple D/V formula - works but assumes constant speed
 * Week 2: Revisited kinematics from physics class - that's the extended formula!
 * Week 3: Derived extended TTC formula with deceleration (took forever!)
 * Week 4: Implemented, tested extensively, verified against MATLAB
 * 
 * FORMULA DERIVATION NOTES (in case I forget):
 * 
 * BASIC TTC: TTC = D / V
 * - Simplest case: assume objects maintain constant velocity
 * - Over-estimates danger (doesn't account for braking)
 * - Good for fast detection baseline
 * 
 * EXTENDED TTC with deceleration:
 * - Start with kinematic equation: D = V*t - (1/2)*a*t²
 * - Rearrange: (1/2)*a*t² - V*t + D = 0  (quadratic form)
 * - Use quadratic formula: t = (-b ± sqrt(b² - 4ac)) / 2a
 * - Here: a=1/2*a_dcel, b=-V, c=D
 * - Simplifies to: TTC = (-V + sqrt(V² + 2*a*D)) / a
 * - Take + root (collision happens at first intersection)
 * - Result: time until objects meet WITH deceleration
 * 
 * TESTING INSIGHTS:
 * - Extended formula must account for BOTH objects' braking capability
 * - If only one brakes: use half their deceleration? (not implemented)
 * - Edge case: when discriminant < 0: collision unavoidable at this deceleration
 * - VALIDATION: Tested against MATLAB synthetic kinematic scenarios ✓
 * 
 * TODO: Implement per-object deceleration (we assume vehicle braking)
 * TODO: Add IMU-based deceleration for more realism
 */

#include "circular_buffer.h"
#include "config/config.h"
#include "config/arduino_compat.h"
#include <cmath>

/**
 * @class TTCCalculator
 * @brief Computes Time-to-Collision metrics from distance history
 */
class TTCCalculator {
public:
    /**
     * @struct TTCResult
     * @brief Complete TTC calculation output
     */
    struct TTCResult {
        float ttc_basic_s;            ///< TTC assuming constant velocity
        float ttc_extended_s;         ///< TTC with braking model
        float closing_velocity_ms;    ///< Rate at which distance is closing (m/s)
        bool valid;                   ///< True if both velocity and TTC are valid
    };
    
private:
    CircularBuffer<DistanceTimestamp, SystemConfig::DISTANCE_HISTORY_SIZE> distance_history;
    
    /**
     * @brief Compute closing velocity from distance history
     * @return Velocity in m/s (positive = gap closing)
     * 
     * Uses oldest and newest measurements to calculate rate of change:
     * V_closing = (D_oldest - D_newest) / (t_newest - t_oldest)
     * 
     * Positive velocity means distance is decreasing (collision risk).
     * Negative velocity means objects moving apart (no risk).
     */
    float computeClosingVelocity() const {
        if (distance_history.size() < 2) {
            return 0.0f;  // Not enough data points
        }
        
        // Get oldest and newest readings
        const DistanceTimestamp& oldest = distance_history.oldest();
        const DistanceTimestamp& newest = distance_history.newest();
        
        // Calculate time delta in seconds
        int32_t delta_time_ms = (int32_t)newest.timestamp_ms - (int32_t)oldest.timestamp_ms;
        if (delta_time_ms <= 0) {
            return 0.0f;  // Invalid time ordering
        }
        float delta_time_s = delta_time_ms / 1000.0f;
        
        // Calculate distance delta in meters (convert cm to m)
        float delta_distance_m = (oldest.distance_cm - newest.distance_cm) / 100.0f;
        
        // Velocity = distance change / time change
        // Positive: gap closing, Negative: gap opening
        float velocity = delta_distance_m / delta_time_s;
        
        return velocity;
    }
    
public:
    /**
     * @brief Initialize empty history buffer
     */
    TTCCalculator() {}
    
    /**
     * @brief Add distance measurement to history
     * @param distance_cm Current distance in centimeters
     * 
     * Stores measurement with current timestamp. If buffer is full,
     * oldest measurement is discarded automatically.
     */
    void addDistanceReading(float distance_cm) {
        uint32_t timestamp = millis();
        DistanceTimestamp reading(distance_cm, timestamp);
        distance_history.push(reading);
    }
    
    /**
     * @brief Calculate TTC metrics based on current history
     * @param deceleration_ms2 Vehicle deceleration in m/s²
     * @return TTCResult with both basic and extended TTC calculations
     * 
     * Requires at least 2 distance measurements in history.
     * Returns invalid result if insufficient data or invalid velocity.
     * 
     * Formulas:
     * - TTC_basic = D / V  (constant velocity assumption)
     * - TTC_extended = (-V + sqrt(V² + 2*a*D)) / a  (with deceleration)
     * 
     * Both formulas assume distance D is in meters, V in m/s, a in m/s².
     * Results are clamped to [0, 99] seconds.
     */
    TTCResult calculate(float deceleration_ms2) {
        TTCResult result = {0.0f, 0.0f, 0.0f, false};
        
        // Need at least 2 data points for velocity calculation
        if (distance_history.size() < 2) {
            return result;  // Not enough history yet
        }
        
        // Compute closing velocity
        float velocity_ms = computeClosingVelocity();
        result.closing_velocity_ms = velocity_ms;
        
        // Guard against invalid velocity
        if (velocity_ms < TTCConfig::MIN_CLOSING_VELOCITY_MS) {
            // Objects not approaching or moving apart
            result.ttc_basic_s = 99.0f;
            result.ttc_extended_s = 99.0f;
            result.valid = true;  // Technically valid: no collision
            return result;
        }
        
        // Get current distance (newest measurement)
        float distance_m = distance_history.newest().distance_cm / 100.0f;
        
        // Clamp distance to positive value
        if (distance_m <= 0.0f) {
            distance_m = 0.01f;  // Minimum distance
        }
        
        // ===== BASIC TTC =====
        // Assumes objects maintain same velocity (no braking)
        // TTC = Distance / Velocity
        result.ttc_basic_s = distance_m / velocity_ms;
        
        // ===== EXTENDED TTC =====
        // Accounts for deceleration: (-V + sqrt(V² + 2*a*D)) / a
        // This models the case where the target object is braking
        // Formula derived from: D = V*t - (1/2)*a*t²
        
        if (deceleration_ms2 < 0.01f) {
            // Very small deceleration - treat as zero
            result.ttc_extended_s = result.ttc_basic_s;
        } else {
            // Compute discriminant: V² + 2*a*D
            float discriminant = (velocity_ms * velocity_ms) + 
                                (2.0f * deceleration_ms2 * distance_m);
            
            if (discriminant < 0.0f) {
                // Collision already inevitable at current deceleration
                result.ttc_extended_s = 0.0f;
            } else {
                // Standard formula: (-V + sqrt(V² + 2*a*D)) / a
                float sqrt_term = sqrt(discriminant);
                result.ttc_extended_s = (-velocity_ms + sqrt_term) / deceleration_ms2;
            }
        }
        
        // Clamp both to reasonable range
        const float MAX_TTC = 99.0f;
        if (result.ttc_basic_s > MAX_TTC) result.ttc_basic_s = MAX_TTC;
        if (result.ttc_extended_s > MAX_TTC) result.ttc_extended_s = MAX_TTC;
        
        // Ensure non-negative (shouldn't happen with valid inputs)
        if (result.ttc_basic_s < 0.0f) result.ttc_basic_s = 0.0f;
        if (result.ttc_extended_s < 0.0f) result.ttc_extended_s = 0.0f;
        
        result.valid = true;
        return result;
    }
    
    /**
     * @brief Clear distance history
     * Useful for system reset or when measurements become unreliable
     */
    void reset() {
        distance_history.clear();
    }
    
    /**
     * @brief Get number of distance readings in history
     * @return Count (0 to DISTANCE_HISTORY_SIZE)
     */
    size_t getHistorySize() const {
        return distance_history.size();
    }
};

#endif // TTC_CALCULATOR_H
