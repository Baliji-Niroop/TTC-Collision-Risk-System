#pragma once

#include "../config/arduino_compat.h"
#include "../config/config.h"
#include "../config/kalman_filter.h"
#include <Wire.h>

#if USE_VL53L1X && defined(ARDUINO) && defined(__has_include)
#if __has_include(<Adafruit_VL53L1X.h>)
#include <Adafruit_VL53L1X.h>
#define HAS_VL53L1X 1
#endif
#endif

// Pins
static const uint8_t PIN_TRIG_1 = 5;
static const uint8_t PIN_ECHO_1 = 18;
static const uint8_t PIN_TRIG_2 = 4;
static const uint8_t PIN_ECHO_2 = 16;
static const uint8_t PIN_ENCODER_A = 19;
static const uint8_t PIN_ENCODER_B = 23;

#ifdef HAS_VL53L1X
static Adafruit_VL53L1X vl53;
#endif

static KalmanFilter1D kalmanFilter;
static float currentDistanceCm = DEFAULT_DISTANCE_CM;

// Encoder state
volatile long encoderPulses = 0;
unsigned long lastEncoderTime = 0;
float hostSpeedKmh = 0.0f;

// Encoder ISR
void IRAM_ATTR encoderISR() {
    int b = digitalRead(PIN_ENCODER_B);
    if (b > 0) encoderPulses++;
    else encoderPulses--;
}

inline void initSensors() {
  pinMode(PIN_TRIG_1, OUTPUT);
  pinMode(PIN_ECHO_1, INPUT);
  pinMode(PIN_TRIG_2, OUTPUT);
  pinMode(PIN_ECHO_2, INPUT);
  
  pinMode(PIN_ENCODER_A, INPUT_PULLUP);
  pinMode(PIN_ENCODER_B, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(PIN_ENCODER_A), encoderISR, RISING);

#ifdef HAS_VL53L1X
  if (vl53.begin(0x29, &Wire)) {
    vl53.startRanging();
  }
#endif
  kalmanInit(&kalmanFilter, 0.01f, 0.5f, 1.0f);
  lastEncoderTime = millis();
}

inline float readUltrasonicBase(uint8_t trigPin, uint8_t echoPin) {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  unsigned long duration = pulseIn(echoPin, HIGH, 30000UL); // 30ms timeout
  if (duration == 0UL) {
    return -1.0f;
  }
  return (duration * 0.0343f) * 0.5f;
}

inline float readVL53L1X() {
#ifdef HAS_VL53L1X
  if (vl53.dataReady()) {
    int16_t distance = vl53.distance();
    vl53.clearInterrupt();
    return distance / 10.0f; // mm to cm
  }
#endif
  return -1.0f;
}

inline float fuseDistance() {
  float d_us = readUltrasonicBase(PIN_TRIG_1, PIN_ECHO_1);
  float d_lidar = readVL53L1X();
  
  // Graceful fallback to mocked LIDAR if VL53L1X missing
  if (d_lidar < 0) {
      d_lidar = readUltrasonicBase(PIN_TRIG_2, PIN_ECHO_2);
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

inline void updateHostSpeed() {
    unsigned long now = millis();
    float dtSeconds = (now - lastEncoderTime) / 1000.0f;
    if (dtSeconds > 0.0f) {
        // Assume 20 pulses per wheel revolution, 0.33m wheel circumference
        float revolutions = abs(encoderPulses) / 20.0f;
        float distanceMeters = revolutions * 0.33f;
        hostSpeedKmh = (distanceMeters / dtSeconds) * 3.6f;
        encoderPulses = 0;
        lastEncoderTime = now;
    }
}

inline float readHostSpeedKmh() {
    updateHostSpeed();
    return hostSpeedKmh;
}

inline float computeConfidence(float distanceCm) {
    float confidence = 0.90f;
    
    // Drop confidence near limits
    if (distanceCm < 10.0f || distanceCm > 400.0f) {
        confidence -= 0.30f;
    }
    // Drop if variance is high vs kalman filter (noisy)
    if (abs(distanceCm - kalmanFilter.x) > 20.0f) {
        confidence -= 0.20f;
    }
    
    if (confidence < 0.1f) return 0.1f;
    if (confidence > 0.99f) return 0.99f;
    return confidence;
}
