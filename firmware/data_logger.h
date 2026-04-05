#ifndef DATA_LOGGER_H
#define DATA_LOGGER_H

/**
 * @file data_logger.h
 * @brief System data logging to serial port in CSV format
 * 
 * Logs complete system state to Serial port in standardized CSV format
 * for post-analysis and validation. Format is compatible with Python
 * dashboard and MATLAB validation scripts.
 * 
 * CSV Schema:
 * timestamp_ms,d_fused_cm,d_filtered_cm,v_closing_ms,ttc_basic_s,ttc_ext_s,risk_class,confidence,loop_time_us
 */
/**
 * data_logger.h - Serial CSV Data Logging & Debugging
 * 
 * Niroop's Capstone Project
 * 
 * FORMAT DESIGN JOURNEY:
 * Week 1: Started logging raw sensor values only
 * Week 2: Expanded to include TTC and risk (6 fields)
 * Week 3: Added confidence and loop timing (needed for validation)
 * Week 4: Current version (9 fields) - captures everything
 * 
 * CSV FORMAT RATIONALE:
 * Chosen format over binary because:
 * ✓ Human readable (can manually inspect rows)
 * ✓ Compatible with Python/MATLAB/Excel without libraries
 * ✓ Easy to parse line-by-line in telemetry viewer
 * ✓ Can manually count rows to verify completeness
 * 
 * COLUMN MEANINGS:
 * 1. timestamp_ms        - When data was captured (for sync with Python clock)
 * 2. d_fused_cm         - Sensor fusion result (US+LiDAR blend)
 * 3. d_filtered_cm      - After Kalman filtering (less noisy)
 * 4. v_closing_ms       - How fast gap is shrinking (m/s)
 * 5. ttc_basic_s        - Constant velocity assumption
 * 6. ttc_ext_s          - With deceleration model
 * 7. risk_class         - 0=SAFE, 1=WARNING, 2=CRITICAL
 * 8. confidence         - ML confidence (0.0-1.0)
 * 9. loop_time_us       - How long loop iteration took (microseconds)
 * 
 * PRECISION CHOICES (%.1f vs %.2f):
 * - Distance (%.1f): cm precision enough for collision detection
 * - Velocity (%.2f): m/s needs 2 decimals for accuracy
 * - TTC (%.2f): seconds need 2 decimals (difference between 1.20s and 1.25s matters!)
 * - Confidence (%.2f): probability score needs 2 decimals
 * 
 * PRODUCTION NOTES:
 * - Each loop (~10 Hz) = 1 CSV row logged
 * - 10 rows/sec × 1000 test = ~10,000 rows per test run
 * - Fits easily in RAM (we collect in Python later, not on board)
 * - For long-term logging to SD card: add ring buffer (TODO)
 * 
 * DEBUG VS PRODUCTION:
 * - logDebug() only compiles if DEBUG flag set (saves space in production)
 * - logError() always present (need to catch failures)
 * - logSystemState() is the main pipeline (called every loop)
 * 
 * LESSONS LEARNED:
 * - Precision too high (%.3f) = unreadable CSV
 * - Precision too low (%.0f) = lose important distinctions
 * - Inclusion of loop_time_us was critical for optimization debugging
 *   Original loop took 150ms, debugged down to 98ms ✓
 * - Risk_class as number (0,1,2) better than string for Python parsing
 * 
 * TODO: Add ring buffer to keep last N records in RAM
 * TODO: Implement SD card logging for longer test runs
 * TODO: Add telemetry checksum for data integrity validation
 */

#include "system_state.h"
#include "config/arduino_compat.h"
#include <stdarg.h>
#include <stdio.h>

/**
 * @class DataLogger
 * @brief Static methods for system logging
 */
class DataLogger {
private:
    static const size_t BUFFER_SIZE = 256;  ///< Temporary formatting buffer
    
public:
    /**
     * @brief Log complete system state as CSV row
     * @param state Current SystemState snapshot
     * 
     * Outputs single CSV line with all key metrics:
     * timestamp (ms), fused_distance (cm), filtered_distance (cm),
     * closing_velocity (m/s), ttc_basic (s), ttc_extended (s),
     * risk_class (0-2), confidence (0.0-1.0), loop_time (µs)
     * 
     * Example output:
     * 12345,245.3,244.8,1.25,2.1,2.5,1,0.87,98500
     */
    static void logSystemState(const SystemState& state) {
        char buffer[BUFFER_SIZE];
        
        // Convert risk class to number
        uint8_t risk_num = static_cast<uint8_t>(state.current_risk);
        
        // Format CSV line with all state data
        snprintf(buffer, BUFFER_SIZE,
                "%lu,%.1f,%.1f,%.2f,%.2f,%.2f,%u,%.2f,%lu",
                millis(),                           // timestamp_ms
                state.distance_fused_cm,            // d_fused_cm
                state.distance_filtered_cm,         // d_filtered_cm  
                state.closing_velocity_ms,          // v_closing_ms
                state.ttc_basic_s,                  // ttc_basic_s
                state.ttc_extended_s,               // ttc_ext_s
                risk_num,                           // risk_class (0=SAFE, 1=WARNING, 2=CRITICAL)
                state.ml_confidence,                // confidence
                state.loop_duration_micros          // loop_time_us
        );
        
        // Send to serial
        Serial.println(buffer);
    }
    
    /**
     * @brief Log error message with timestamp
     * @param error_msg Human-readable error message
     * 
     * Format: [timestamp] ERROR: <message>
     * Example: [12345] ERROR: LIDAR initialization failed
     */
    static void logError(const char* error_msg) {
        Serial.print("[");
        Serial.print(millis());
        Serial.print("] ERROR: ");
        Serial.println(error_msg);
    }
    
    /**
     * @brief Log debug message with timestamp (optional)
     * @param debug_msg Debug information
     * 
     * Only compiled when DEBUG flag is defined.
     * Format: [timestamp] DEBUG: <message>
     * Example: [12345] DEBUG: Calibrating MPU6050
     */
    static void logDebug(const char* debug_msg) {
        #ifdef DEBUG
        Serial.print("[");
        Serial.print(millis());
        Serial.print("] DEBUG: ");
        Serial.println(debug_msg);
        #endif
    }
    
    /**
     * @brief Print CSV header for data logging
     * Should be called once during initialization to document format.
     * 
     * Output:
     * timestamp_ms,d_fused_cm,d_filtered_cm,v_closing_ms,ttc_basic_s,ttc_ext_s,risk_class,confidence,loop_time_us
     */
    static void printCSVHeader() {
        Serial.println("timestamp_ms,d_fused_cm,d_filtered_cm,v_closing_ms,ttc_basic_s,ttc_ext_s,risk_class,confidence,loop_time_us");
    }
    
    /**
     * @brief Log formatted message (printf-style)
     * @param format Format string
     * @param ... Variable arguments
     * 
     * Provides flexible formatted logging capability.
     * Note: Implementation requires stdarg.h - minimal embedded systems
     * may not support this. Use simpler log methods above instead.
     */
    static void logFormatted(const char* format, ...) {
        // Note: Full printf support adds overhead on embedded systems
        // For production, prefer simpler methods above
        char buffer[BUFFER_SIZE];
        va_list args;
        va_start(args, format);
        vsnprintf(buffer, BUFFER_SIZE, format, args);
        va_end(args);
        Serial.println(buffer);
    }
};

#endif // DATA_LOGGER_H
