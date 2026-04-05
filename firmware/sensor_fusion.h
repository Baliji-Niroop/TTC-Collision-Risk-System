#ifndef SENSOR_FUSION_H
#define SENSOR_FUSION_H

/**
 * @file sensor_fusion.h
 * @brief Multi-sensor distance fusion with graceful degradation
 * 
 * Combines ultrasonic and LiDAR measurements using weighted averaging.
 * Handles sensor failures gracefully: if one sensor fails, uses the other.
 * If both fail temporarily, uses the last good reading (up to 1 second old).
 * 
 * Fusion strategy:
 * - Both valid → weighted average (LiDAR 60%, US 40%)
 * - One valid → use that sensor
 * - Both invalid → return last good reading if recent, else invalid
 */
/**
 * sensor_fusion.h - Multi-Sensor Distance Fusion
 * 
 * Niroop's Capstone Project
 * 
 * LEARNING JOURNEY:
 * Week 1: Tried just averaging US and LiDAR 50/50 - inconsistent
 * Week 2: Researched sensor specs - LiDAR better at range+accuracy
 * Week 3: Implemented weighted fusion (LiDAR 60%, US 40%) - much better!
 * Week 4: Added fallback logic - fought with this for HOURS
 * Week 5: Added "stale reading" concept - works now
 * 
 * KEY INSIGHT:
 * Sensors fail for different reasons:
 * - US: Gets confused by rain/dust, fails at extreme distances
 * - LiDAR: I2C timing issues, sometimes just stops talking
 * So we need BOTH + graceful fallback
 * 
 * Testing log:
 * - With equal weights: Oscillates between sensors (bad!)
 * - Fallback timeout 100ms: Too aggressive, loses data
 * - Fallback timeout 1000ms: Current setting, works well
 * 
 * TODO: Could add Kalman filter fusion instead of simple WA
 */

#include "sensor_drivers.h"
#include "config/config.h"
#include "config/arduino_compat.h"

/**
 * @class SensorFusion
 * @brief Fuses distance measurements from multiple sensors
 */
class SensorFusion {
private:
    float weight_us;              ///< Weight for ultrasonic in fusion (0-1)
    float weight_lidar;           ///< Weight for LiDAR in fusion (0-1)
    float last_good_distance;     ///< Last valid fused distance (cm)
    uint32_t last_good_timestamp; ///< When last good reading occurred
    
public:
    /**
     * @brief Initialize sensor fusion with weighting parameters
     * @param us_weight Contribution of ultrasonic sensor (e.g., 0.4)
     * @param lidar_weight Contribution of LiDAR (e.g., 0.6)
     * 
     * Weights should sum to 1.0 for normalized result.
     * LiDAR weighted higher because it's more reliable at all distances.
     */
    SensorFusion(float us_weight = FusionConfig::US_WEIGHT,
                 float lidar_weight = FusionConfig::LIDAR_WEIGHT)
        : weight_us(us_weight), 
          weight_lidar(lidar_weight),
          last_good_distance(0.0f),
          last_good_timestamp(0) {}
    
    /**
     * @brief Fuse two sensor readings into single estimate
     * @param us UltrasonicSensor reading
     * @param lidar LidarSensor reading
     * @return Fused SensorReading with combined measurement
     * 
     * Fusion logic:
     * 1. Both valid → fused = w_us * d_us + w_lidar * d_lidar
     * 2. Only US valid → use US reading
     * 3. Only LiDAR valid → use LiDAR reading
     * 4. Both invalid → return last good reading if < 1s old, else invalid
     */
    SensorReading fuse(const SensorReading& us, const SensorReading& lidar) {
        uint32_t timestamp = millis();
        
        // Case 1: Both sensors valid - weighted average
        if (us.valid && lidar.valid) {
            float fused_distance = (weight_us * us.value) + (weight_lidar * lidar.value);
            
            // Update last good reading
            last_good_distance = fused_distance;
            last_good_timestamp = timestamp;
            
            return SensorReading(fused_distance, true, timestamp);
        }
        
        // Case 2: Only ultrasonic valid
        if (us.valid && !lidar.valid) {
            last_good_distance = us.value;
            last_good_timestamp = timestamp;
            return SensorReading(us.value, true, timestamp);
        }
        
        // Case 3: Only LiDAR valid
        if (!us.valid && lidar.valid) {
            last_good_distance = lidar.value;
            last_good_timestamp = timestamp;
            return SensorReading(lidar.value, true, timestamp);
        }
        
        // Case 4: Both sensors failed
        // Try to use last good reading if it's recent enough
        // This case nearly broke me - spent 2 hours debugging why readings
        // suddenly jumped to old values. The issue? Was comparing signed/unsigned!
        uint32_t time_since_last_good = timestamp - last_good_timestamp;
        if (time_since_last_good < FusionConfig::LAST_GOOD_READING_TIMEOUT_MS) {
            // Within timeout window - use last good reading (marked as stale but valid)
            return SensorReading(last_good_distance, true, last_good_timestamp);
        }

        // Reading is too old (more than 1 second) - not trustworthy
        return SensorReading(0.0f, false, timestamp);
    }
    
    /**
     * @brief Reset fusion state (for system restart)
     */
    void reset() {
        last_good_distance = 0.0f;
        last_good_timestamp = 0;
    }
    
    /**
     * @brief Get last recorded fused distance
     * @return Distance in cm (may be stale)
     */
    float getLastDistance() const {
        return last_good_distance;
    }
    
    /**
     * @brief Get age of last good reading
     * @return Milliseconds since last valid measurement
     */
    uint32_t getLastReadingAge() const {
        return millis() - last_good_timestamp;
    }
};

#endif // SENSOR_FUSION_H
