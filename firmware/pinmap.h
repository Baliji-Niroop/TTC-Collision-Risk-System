#ifndef PINMAP_H
#define PINMAP_H

/**
 * pinmap.h - Unified Pin Definitions for TTC Wokwi Simulator
 * 
 * Single source of truth for all hardware pin mappings.
 * Pin assignments are synchronized with:
 *   - diagram.json (circuit connections)
 *   - wokwi_serial_bridge.py (mock data if needed)
 *   - firmware components
 * 
 * ESP32 DevKit-V1 pinout reference:
 *   https://randomnerdtutorials.com/esp32-pinout-reference-gpios/
 * 
 * Design principles:
 *   - One definition per pin - no duplication
 *   - Grouped by functional category (sensors, outputs, I2C, SPI, etc.)
 *   - Each pin labeled with connected component and Wokwi diagram ID
 *   - Type-safe (static const uint8_t preferred over #define)
 */

#include <stdint.h>

// ============================================
// ULTRASONIC SENSORS (HC-SR04)
// ============================================
// Primary sonar unit (front-facing obstacle detection)
static const uint8_t PIN_SONAR1_TRIG = 5;      // TRIG → esp:D5 (Wokwi: sonar)
static const uint8_t PIN_SONAR1_ECHO = 18;     // ECHO → esp:D18 (Wokwi: sonar)

// Secondary sonar unit (rear or alternate detection)
static const uint8_t PIN_SONAR2_TRIG = 4;      // TRIG → esp:D4 (Wokwi: sonar2)
static const uint8_t PIN_SONAR2_ECHO = 16;     // ECHO → esp:D16 (Wokwi: sonar2)

// ============================================
// I2C BUS (Shared by multiple sensors)
// ============================================
// Standard I2C interface on ESP32
static const uint8_t PIN_I2C_SDA = 21;         // SDA → esp:D21 (Wokwi: oled, imu)
static const uint8_t PIN_I2C_SCL = 22;         // SCL → esp:D22 (Wokwi: oled, imu)

// I2C Devices on this bus:
//   - 0x3C: OLED Display (SSD1306)
//   - 0x68: MPU6050 (Accelerometer/Gyro)
//   - 0x29: VL53L1X (ToF LIDAR) - optional

// ============================================
// WHEEL ENCODER (Rotary Encoder / KY-040)
// ============================================
// For host vehicle speed measurement
static const uint8_t PIN_ENCODER_CLK = 19;    // CLK → esp:D19 (Wokwi: encoder)
static const uint8_t PIN_ENCODER_DT  = 23;    // DT → esp:D23 (Wokwi: encoder)
// Note: Encoder also has a push button (SW) - not currently wired

// ============================================
// LED ALERT BAR (Visual Risk Indicators)
// ============================================
// Green (SAFE) - Two LEDs for visibility
static const uint8_t PIN_LED_SAFE1 = 25;      // → esp:D25, ledSafe1 (green)
static const uint8_t PIN_LED_SAFE2 = 26;      // → esp:D26, ledSafe2 (green)

// Yellow (WARNING) - Two LEDs for visibility
static const uint8_t PIN_LED_WARNING1 = 27;   // → esp:D27, ledWarning1 (yellow)
static const uint8_t PIN_LED_WARNING2 = 14;   // → esp:D14, ledWarning2 (yellow)

// Red (CRITICAL) - Single LED, highest alert
static const uint8_t PIN_LED_CRITICAL = 12;   // → esp:D12, ledCritical (red)

// ============================================
// BUZZER (Audible Alert)
// ============================================
static const uint8_t PIN_BUZZER = 32;          // → esp:D32, buzzer

// ============================================
// 3.3V POWER RAIL PINS (for reference)
// ============================================
// Wokwi connections using VIN/3V3/GND:
//   - OLED: 3V3, GND
//   - MPU6050: 3V3, GND
//   - Encoders: VIN, GND
//   - HC-SR04s: VIN, GND
// These are implicit in diagram.json but documented here for completeness.

// ============================================
// Pin Grouping Helpers (for init/shutdown)
// ============================================

// LED pins for alert output
static const uint8_t LED_PINS[] = {
    PIN_LED_SAFE1,
    PIN_LED_SAFE2,
    PIN_LED_WARNING1,
    PIN_LED_WARNING2,
    PIN_LED_CRITICAL
};
static const uint8_t NUM_LED_PINS = 5;

// Sonar pins
static const uint8_t SONAR_PINS[] = {
    PIN_SONAR1_TRIG,
    PIN_SONAR1_ECHO,
    PIN_SONAR2_TRIG,
    PIN_SONAR2_ECHO
};
static const uint8_t NUM_SONAR_PINS = 4;

#endif // PINMAP_H
