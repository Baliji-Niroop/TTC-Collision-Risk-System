#pragma once

/**
 * sensors.h - Unified Sensor Interface for TTC
 * 
 * Provides readings from:
 *   - Ultrasonic sensors (HC-SR04) x2 for distance
 *   - Wheel encoder (KY-040) for host speed
 *   - LIDAR (VL53L1X, optional) via I2C
 *   - Kalman filter for sensor fusion
 * 
 * Pin assignments sourced from pinmap.h (centralized).
 * All calculations use standardized units (cm, km/h, m/s²).
 */

#include "../config/arduino_compat.h"
#include "../config/config.h"
#include "../pinmap.h"
#include "../config/kalman_filter.h"
#include <Wire.h>

// ============================================
// SENSOR HARDWARE
// ============================================

#if USE_VL53L1X && defined(ARDUINO) && defined(__has_include)
#if __has_include(<Adafruit_VL53L1X.h>)
#include <Adafruit_VL53L1X.h>
#define HAS_VL53L1X 1
#endif
#endif

#ifdef HAS_VL53L1X
static Adafruit_VL53L1X vl53;
#endif

// ============================================
// SENSOR STATE
// ============================================

// Distance measurement (fused from all sources)
static KalmanFilter1D kalmanFilter;
static float currentDistanceCm = DEFAULT_DISTANCE_CM;

// Encoder-based speed measurement
extern volatile long encoderPulses;
extern unsigned long lastEncoderTime;
float hostSpeedKmh = 0.0f;

// ============================================
// ENCODER INTERRUPT HANDLER
// ============================================

/**
 * Encoder CLK rising edge interrupt
 * Counts pulses in forward/backward direction based on DT pin level
 */
void IRAM_ATTR encoderISR() {
    int dt_state = digitalRead(PIN_ENCODER_DT);
    if (dt_state > 0) {
        encoderPulses++;
    } else {
        encoderPulses--;
    }
}

// ============================================
// INITIALIZATION
// ============================================

/**
 * Initialize all sensor hardware:
 *   - Configure GPIO pins for sonar TRIG/ECHO
 *   - Attach encoder interrupt
 *   - Initialize I2C LIDAR if available
 *   - Setup Kalman filter for fusion
 */
inline void initSensors() {
  // Ultrasonic sensors GPIO
  pinMode(PIN_SONAR1_TRIG, OUTPUT);
  pinMode(PIN_SONAR1_ECHO, INPUT);
  pinMode(PIN_SONAR2_TRIG, OUTPUT);
  pinMode(PIN_SONAR2_ECHO, INPUT);
  
  // Encoder GPIO with pull-ups
  pinMode(PIN_ENCODER_CLK, INPUT_PULLUP);
  pinMode(PIN_ENCODER_DT, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(PIN_ENCODER_CLK), encoderISR, RISING);

  // Optional LIDAR initialization
#ifdef HAS_VL53L1X
  if (vl53.begin(0x29, &Wire)) {
    vl53.startRanging();
  }
#endif

  // Kalman filter for distance smoothing
  kalmanInit(&kalmanFilter, KALMAN_Q, KALMAN_R, 1.0f);
  lastEncoderTime = millis();
}

// ============================================
// ULTRASONIC DISTANCE READING
// ============================================

/**
 * Read single HC-SR04 ultrasonic sensor
 * 
 * Triggers pulse on TRIG pin, measures echo time on ECHO pin.
 * Distance = (echo_time_µs * speed_of_sound / 2)
 * 
 * Args:
 *   trigPin: GPIO for ultrasonic TRIG line
 *   echoPin: GPIO for ultrasonic ECHO line
 *   
 * Returns:
 *   Distance in cm, or -1.0f if timeout/error
 */
inline float readUltrasonicBase(uint8_t trigPin, uint8_t echoPin) {
  // Generate 10µs pulse on trigger pin
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  // Measure echo pulse duration (30ms timeout)
  unsigned long duration = pulseIn(echoPin, HIGH, 30000UL);
  if (duration == 0UL) {
    return -1.0f;
  }
  
  // Distance = (duration * speed_of_sound / 2)
  // Speed of sound = 0.0343 cm/µs ≈ 343 m/s at 20°C
  return (duration * 0.0343f) * 0.5f;
}

// ============================================
// LIDAR DISTANCE READING (Optional)
// ============================================

/**
 * Read VL53L1X time-of-flight (ToF) LIDAR
 * 
 * More accurate than ultrasonic, especially at longer ranges.
 * Requires Adafruit_VL53L1X library and I2C connection.
 * 
 * Returns:
 *   Distance in cm, or -1.0f if not available/not ready
 */
inline float readVL53L1X() {
#ifdef HAS_VL53L1X
  if (vl53.dataReady()) {
    int16_t distance = vl53.distance();
    vl53.clearInterrupt();
    return distance / 10.0f;  // Convert mm to cm
  }
#endif
  return -1.0f;
}

// ============================================
// SENSOR FUSION
// ============================================

/**
 * Fuse distance readings from all available sources
 * 
 * Strategy:
 *   - Primary: Read both sonar sensors
 *   - Secondary: Read LIDAR if available, otherwise sonar2 as fallback
 *   - Weights: 40% ultrasonic, 60% LIDAR (LIDAR more accurate)
 *   - Smoothing: Apply Kalman filter to reduce noise
 * 
 * Returns:
 *   Filtered distance in cm from kalmanFilter state
 */
inline float fuseDistance() {
  float d_us = readUltrasonicBase(PIN_SONAR1_TRIG, PIN_SONAR1_ECHO);
  float d_lidar = readVL53L1X();
  
  // Graceful fallback to secondary sonar if LIDAR missing
  if (d_lidar < 0) {
      d_lidar = readUltrasonicBase(PIN_SONAR2_TRIG, PIN_SONAR2_ECHO);
  }

  float fused = -1.0f;
  if (d_us > 0.0f && d_lidar > 0.0f) {
      fused = 0.40f * d_us + 0.60f * d_lidar;
  } else if (d_us > 0.0f) {
      fused = d_us;
  } else if (d_lidar > 0.0f) {
      fused = d_lidar;
  }
  
  if (fused > 0.0f) {
      currentDistanceCm = kalmanUpdate(&kalmanFilter, fused);
  }
  return currentDistanceCm;
}

inline float readDistanceCm(unsigned long timestampMs = 0) {
  return fuseDistance();
}

// ============================================
// SPEED MEASUREMENT (ENCODER)
// ============================================

/**
 * Update host vehicle speed from encoder pulses
 * 
 * Calculation:
 *   - Pulses counted in encoderISR()
 *   - Assumes 20 pulses per wheel revolution
 *   - Wheel circumference: 0.33m (65mm diameter)
 *   - Speed = distance / time * 3.6 (to convert m/s to km/h)
 *   
 * Resets pulse counter after each update.
 */
inline void updateHostSpeed() {
    unsigned long now = millis();
    float dtSeconds = (now - lastEncoderTime) / 1000.0f;
    if (dtSeconds > 0.0f) {
        // 20 pulses per revolution, 0.33m circumference
        float revolutions = abs(encoderPulses) / 20.0f;
        float distanceMeters = revolutions * 0.33f;
        hostSpeedKmh = (distanceMeters / dtSeconds) * 3.6f;
        encoderPulses = 0;
        lastEncoderTime = now;
    }
}

/**
 * Read current host vehicle speed in km/h
 * Updates internal state, returns cached value
 */
inline float readHostSpeedKmh() {
    updateHostSpeed();
    return hostSpeedKmh;
}

// ============================================
// CONFIDENCE ESTIMATION
// ============================================

/**
 * Estimate measurement confidence based on reading quality
 * 
 * Factors:
 *   - 90% baseline confidence
 *   - -30% if distance is at sensor limits (< 10cm or > 400cm)
 *   - -20% if sensor reading is noisy (variance > 20cm from Kalman estimate)
 *   - Clamped to [0.1, 0.99] range
 * 
 * Used by main.ino to weight telemetry importance.
 * 
 * Args:
 *   distanceCm: Raw distance measurement
 *   
 * Returns:
 *   Confidence score [0.1 to 0.99]
 */
inline float computeConfidence(float distanceCm) {
    float confidence = 0.90f;
    
    // Drop confidence near sensor limits
    if (distanceCm < 10.0f || distanceCm > 400.0f) {
        confidence -= 0.30f;
    }
    
    // Drop if reading is inconsistent with Kalman filter estimate (noisy)
    if (abs(distanceCm - kalmanFilter.x) > 20.0f) {
        confidence -= 0.20f;
    }
    
    // Clamp to valid range
    if (confidence < 0.1f) return 0.1f;
    if (confidence > 0.99f) return 0.99f;
    return confidence;
}
