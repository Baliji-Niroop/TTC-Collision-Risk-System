#ifndef SYSTEM_STATE_H
#define SYSTEM_STATE_H

/**
 * @file system_state.h
 * @brief Global system state snapshot
 * 
 * Aggregates all sensor readings, processed values, and ML outputs
 * into a single struct for logging, monitoring, and display.
 * Provides complete visibility into system status each loop cycle.
 */
/**
 * system_state.h - System State Container & Error Tracking
 * 
 * Niroop's Capstone Project
 * 
 * EVOLUTION NOTES:
 * Week 1: Started with 3 fields (distance, TTC, risk) - grew organically
 * Week 2: Added sensor readings, timing info, error flags as needed
 * Week 3: Realized we need full circle closure - captured at every loop
 * Week 4: Current version - 15 fields tracking everything relevant
 * 
 * PURPOSE OF THIS STRUCT:
 * We need to capture the ENTIRE system state at each 100ms loop cycle
 * For:
 * - CSV logging (database row)
 * - Real-time display status
 * - Post-run analysis in MATLAB
 * - Debugging (what was the state when crash occurred?)
 * 
 * IMPORTANCE OF ERROR FLAGS (Bitfield):
 * Single byte tracks up to 8 different errors using bit positions:
 * - Bit 0: LiDAR init failed
 * - Bit 1: IMU init failed
 * - Bit 2: Both sensors lost
 * - Bit 3: Loop overran 100ms budget
 * 
 * Note: I initially used separate bool fields (REJECTED)
 * - Wasted memory (8 bytes vs 1 byte)
 * - Hard to check "any error"
 * - Bitfield is elegant solution (learned this week!)
 * 
 * CALIBRATION JOURNEY:
 * Initial state (Week 1): All values 0.0f - confusing in logs
 * After testing: Found defaults should be:
 *   - ttc_basic_s = 99.0f (means "safe infinite distance")
 *   - ttc_extended_s = 99.0f (same)
 *   - current_risk = SAFE (default state)
 *   - ml_confidence = 0.0f (no confidence yet)
 * This way, uninitialized state is "safe" not "critical"
 * 
 * TODO: Add timestamp field in loop_start_micros for sync check
 * TODO: Track loop overrun histogram (how many times exceeded 100ms?)
 */

#include "sensor_drivers.h"
#include "ml_classifier.h"
#include <stdint.h>

/**
 * @enum SystemError
 * @brief Bit flags for system error conditions
 */
enum SystemError : uint8_t {
    ERROR_NONE = 0x00,          ///< No errors
    ERROR_LIDAR_INIT = 0x01,    ///< LiDAR failed to initialize
    ERROR_IMU_INIT = 0x02,      ///< IMU failed to initialize
    ERROR_BOTH_SENSORS_FAIL = 0x04,  ///< Both distance sensors failed
    ERROR_LOOP_OVERRUN = 0x08   ///< Loop exceeded 100ms cycle time
};

/**
 * @struct SystemState
 * @brief Complete snapshot of system state for single loop iteration
 */
struct SystemState {
    // ===== Raw Sensor Readings =====
    SensorReading us_reading;           ///< Ultrasonic sensor measurement
    SensorReading lidar_reading;        ///< LiDAR sensor measurement
    SensorReading imu_reading;          ///< IMU acceleration (deceleration)
    SensorReading speed_reading;        ///< Wheel encoder speed measurement
    
    // ===== Processed Distance Data =====
    float distance_fused_cm;            ///< Fused distance from sensors (cm)
    float distance_filtered_cm;         ///< Kalman-filtered distance (cm)
    
    // ===== Computed Metrics =====
    float closing_velocity_ms;          ///< Rate of approach (m/s)
    float ttc_basic_s;                  ///< TTC at constant velocity (s)
    float ttc_extended_s;               ///< TTC with deceleration (s)
    
    // ===== ML Classification =====
    RiskClass current_risk;             ///< Classified risk level
    float ml_confidence;                ///< Confidence in classification (0-1)
    RoadCondition road_condition;       ///< Detected road surface
    
    // ===== Timing Information =====
    uint32_t loop_start_micros;         ///< Timestamp of loop start
    uint32_t loop_duration_micros;      ///< Measured loop execution time
    
    // ===== System Health =====
    bool system_ok;                     ///< Overall system operational status
    uint8_t error_flags;                ///< Bitfield of error conditions
    
    // ===== Constructor =====
    SystemState() : 
        distance_fused_cm(0.0f),
        distance_filtered_cm(0.0f),
        closing_velocity_ms(0.0f),
        ttc_basic_s(99.0f),
        ttc_extended_s(99.0f),
        current_risk(RiskClass::SAFE),
        ml_confidence(0.0f),
        road_condition(RoadCondition::DRY),
        loop_start_micros(0),
        loop_duration_micros(0),
        system_ok(true),
        error_flags(ERROR_NONE) {}
    
    /**
     * @brief Check if specific error flag is set
     * @param error_bit Error flag to check
     * @return True if flag is set
     */
    bool hasError(uint8_t error_bit) const {
        return (error_flags & error_bit) != 0;
    }
    
    /**
     * @brief Set specific error flag
     * @param error_bit Error flag to set
     */
    void setError(uint8_t error_bit) {
        error_flags |= error_bit;
        system_ok = (error_flags == ERROR_NONE);
    }
    
    /**
     * @brief Clear specific error flag
     * @param error_bit Error flag to clear
     */
    void clearError(uint8_t error_bit) {
        error_flags &= ~error_bit;
        system_ok = (error_flags == ERROR_NONE);
    }
    
    /**
     * @brief Clear all errors
     */
    void clearAllErrors() {
        error_flags = ERROR_NONE;
        system_ok = true;
    }
};

#endif // SYSTEM_STATE_H
