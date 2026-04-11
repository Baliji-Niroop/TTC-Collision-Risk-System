#ifndef CONFIG_H
#define CONFIG_H

/**
 * config.h - Niroop's Collision Detection Project
 * 
 * ⚠️ DEPRECATION NOTICE (Added April 11, 2026):
 * 
 * PIN DEFINITIONS IN THIS FILE ARE OUTDATED.
 * =========================================
 * 
 * As of the Wokwi simulator rewrite, all pin definitions have been centralized
 * in firmware/pinmap.h. This file contains legacy pin definitions that CONFLICT
 * with the current design:
 * 
 * OUTDATED (config.h):          CURRENT (pinmap.h):
 *   ENC_CH_A = 34                 PIN_ENCODER_CLK = 19 ✓
 *   ENC_CH_B = 35                 PIN_ENCODER_DT = 23 ✓
 *   LED_YELLOW_2 = 28             PIN_LED_WARNING2 = 14 ✓
 *   LED_RED = 29                  PIN_LED_CRITICAL = 12 ✓
 * 
 * DO NOT use pin definitions from this file. Use firmware/pinmap.h instead.
 * This file is kept for reference/historical purposes only.
 * 
 * ========================================================================
 * 
 * Started: Nov 5, 2024
 * Last modified: Dec 10, 2024
 * Deprecated: April 11, 2026 (replaced by firmware/pinmap.h)
 */

#include <stdint.h>

// ============================================
// PIN DEFINITIONS
// ============================================
// Organized: Nov 28 after sensor integration
// (originally just #define TRIG_PIN 5 etc scattered in main)

// ULTRASONIC SENSOR (HC-SR04)
#define TRIG_PIN 5
#define ECHO_PIN 18

// I2C BUS (both VL53L1X and MPU6050 share this)
#define SDA_PIN 21
#define SCL_PIN 22
// NOTE: Spent 2 hours debugging I2C - thought I had bad sensors
// Actually was double init on Wire.begin(). Fixed by adding check in begin() functions

// WHEEL ENCODER (for speed measurement)
#define ENC_CH_A 34         // Interrupt pin
#define ENC_CH_B 35         // Reference (for direction later)

// LED ALERT BAR
const int LED_GREEN_1 = 25;
const int LED_GREEN_2 = 26;
const int LED_YELLOW_1 = 27;
const int LED_YELLOW_2 = 28;
const int LED_RED = 29;
// TODO: Could use array instead? Would clean this up
// For now keeping individual vars - works and easier to debug

// BUZZER
#define BUZZER_PIN 32

// ============================================
// SENSOR CONSTANTS
// ============================================

// ULTRASONIC (HC-SR04)
#define SOUND_SPEED 0.0343  // cm per microsecond
                            // = ~343 m/s at 20°C
                            // Checked against datasheet: ✓ correct

#define US_TIMEOUT_MS 30    // 30ms timeout for echo
                            // Anything past this = out of range or lost signal
                            // Originally tried 50ms but too many false valid readings

#define US_MIN_RANGE_CM 2   // Sensor spec minimum
#define US_MAX_RANGE_CM 400 // Sensor spec maximum

// LIDAR (VL53L1X)  
// NOTE: Using pololu library version 2.0.8
// Had version conflicts - make sure requirements.txt pins it
#define LIDAR_I2C_ADDR 0x29
#define LIDAR_MIN_RANGE_CM 4
#define LIDAR_MAX_RANGE_CM 800
#define LIDAR_TIMEOUT_MS 50  // measurement timing budget

// MPU6050 (Accelerometer)
#define MPU_I2C_ADDR 0x68
#define MPU_ACCEL_SCALE 16384.0  // for ±2g range
                                  // 1g = 9.81 m/s²
#define MPU_CALIB_SAMPLES 500     // samples to average during calibration
                                  // (was 1000, too slow, 500 works fine)

// ============================================
// KALMAN FILTER TUNING
// ============================================
// These took FOREVER to get right
// Testing log:
//   Q=0.1, R=1.0  → too smooth, responds slowly (rejected)
//   Q=0.01, R=0.1 → too responsive, noisy (rejected)
//   Q=0.01, R=0.5 → GOOD! Used this for all testing (CURRENT)
//
// Lower Q = trust the model more = smoother
// Lower R = trust sensor more = faster response
// Current balance seems best for 100ms updates

#define KALMAN_Q 0.01f
#define KALMAN_R 0.5f

// ============================================
// SENSOR FUSION
// ============================================
// Combining ultrasonic + lidar
// Initially tried 50/50 - lidar is more accurate, so weighted it higher
// Testing showed 60% lidar / 40% ultrasonic works best

#define FUSION_US_WEIGHT 0.4f
#define FUSION_LIDAR_WEIGHT 0.6f

// If both sensors fail, use last good reading if it's within this time
#define SENSOR_FALLBACK_TIME_MS 1000  // 1 second

// ============================================
// TTC THRESHOLDS
// ============================================
// Based on ISO 15623 standard + textbook recommendations
// Converted to seconds (rather than distance) because easier to reason about
// NOTE: These values MUST stay synchronized with src/config.py RISK_THRESHOLDS

#define TTC_CRITICAL_S 1.5      // seconds - TTC <= 1.5s is CRITICAL (highest danger)
#define TTC_WARNING_S 3.0       // seconds - 1.5s < TTC <= 3.0s is WARNING
#define TTC_SAFE_THRESHOLD 3.0  // seconds - TTC > 3.0s is SAFE

// Legacy alias for backward compatibility
#define TTC_WARNING_THRESHOLD TTC_WARNING_S

// Road condition multipliers
// These increase the threshold when roads are slippery
// Dry: 1.0x (no change)
// Wet: 1.4x (from vehicle dynamics textbook - Chapter 5)
// Gravel: 1.6x (conservative estimate)
// Ice: 2.0x (very conservative)

#define MULTIPLIER_WET 1.4f
#define MULTIPLIER_GRAVEL 1.6f
#define MULTIPLIER_ICE 2.0f

// ============================================
// SYSTEM TIMING
// ============================================
#define LOOP_INTERVAL_MS 100        // 10 Hz update rate
                                    // Tried 50ms but I2C + sensor reads couldn't
                                    // complete in time. 100ms is stable with headroom

#define SERIAL_BAUD 115200          // For Serial communication to Python dashboard

// Canonical packet cadence used by firmware/main.ino loop guard.
#ifndef PACKET_INTERVAL_MS
#define PACKET_INTERVAL_MS LOOP_INTERVAL_MS
#endif

// ============================================
// OTHER CONSTANTS
// ============================================
#define DEFAULT_DECEL_MS2 5.0       // m/s² - used if IMU unavailable
                                    // ~typical moderate braking

#define ENCODER_PPR 600             // Pulses per revolution of encoder

// Wheel diameter - measured with calipers
// IMPORTANT: Update this if using different wheels!
#define WHEEL_DIAMETER_M 0.065      // 65mm = 6.5cm

// Minimum closing velocity to consider "approaching"
// Avoids division by zero in TTC calculation
#define MIN_VELOCITY_MS 0.1

// Default seeded distance used before first valid sensor fusion update.
#ifndef DEFAULT_DISTANCE_CM
#define DEFAULT_DISTANCE_CM 400.0f
#endif

// ============================================
// FEATURE FLAGS
// ============================================
// Set to 1 to enable, 0 to disable

#define USE_MPU6050     1
#define USE_VL53L1X     0   // set to 1 only if you buy the VL53L1X LIDAR

// Uncomment to activate the decision tree classifier
// #define ENABLE_ML_CLASSIFIER

// ============================================
// C++ CONFIG NAMESPACES
// ============================================
// Required by ml_classifier.h, sensor_fusion.h, ttc_calculator.h, alert_controller.h
// These wrap scalar #defines into type-safe namespace structs

namespace TTCConfig {
    static const float TTC_SAFE_THRESHOLD_S    = TTC_SAFE_THRESHOLD;
    static const float TTC_WARNING_THRESHOLD_S = TTC_WARNING_S;
    static const float MIN_CLOSING_VELOCITY_MS = MIN_VELOCITY_MS;
}

namespace FusionConfig {
    static const float US_WEIGHT                    = FUSION_US_WEIGHT;
    static const float LIDAR_WEIGHT                 = FUSION_LIDAR_WEIGHT;
    static const uint32_t LAST_GOOD_READING_TIMEOUT_MS = SENSOR_FALLBACK_TIME_MS;
}

namespace SystemConfig {
    static const uint8_t DISTANCE_HISTORY_SIZE = 3;
    static const uint16_t BUZZER_WARNING_FREQ_HZ  = 1000;
    static const uint16_t BUZZER_CRITICAL_FREQ_HZ = 2500;
    static const uint32_t BUZZER_PULSE_MS         = 500;
}

#endif // CONFIG_H
