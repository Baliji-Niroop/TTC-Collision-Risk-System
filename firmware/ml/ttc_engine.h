#pragma once

#include <math.h>

// Circular buffer for distance history over ~200ms
static const uint8_t VELOCITY_HISTORY_SIZE = 3;
static float distanceBuffer[VELOCITY_HISTORY_SIZE] = {0};
static unsigned long timeBuffer[VELOCITY_HISTORY_SIZE] = {0};
static uint8_t bufferIndex = 0;
static uint8_t bufferCount = 0;

inline void pushDistanceHistory(float distanceCm, unsigned long timestampMs) {
  distanceBuffer[bufferIndex] = distanceCm;
  timeBuffer[bufferIndex] = timestampMs;
  bufferIndex = (bufferIndex + 1) % VELOCITY_HISTORY_SIZE;
  if (bufferCount < VELOCITY_HISTORY_SIZE) {
    bufferCount++;
  }
}

// Compute closing speed using the history buffer
inline float computeClosingSpeedKmh(float currentDistanceCm, unsigned long timestampMs) {
  pushDistanceHistory(currentDistanceCm, timestampMs);

  if (bufferCount < VELOCITY_HISTORY_SIZE) {
    return 0.0f; // Not enough data
  }

  uint8_t oldestIdx = bufferIndex;
  uint8_t newestIdx = (bufferIndex + VELOCITY_HISTORY_SIZE - 1) % VELOCITY_HISTORY_SIZE;

  float deltaCm = distanceBuffer[oldestIdx] - distanceBuffer[newestIdx];
  float elapsedSec = (timeBuffer[newestIdx] - timeBuffer[oldestIdx]) / 1000.0f;

  if (elapsedSec > 0.0f && deltaCm > 0.0f) {
    float closingSpeedMps = (deltaCm / 100.0f) / elapsedSec;
    return closingSpeedMps * 3.6f;
  }
  return 0.0f;
}

/*
 * TTC Basic Formula
 * Assumes closing velocity is constant.
 * TTC = distance / closing_velocity
 */
inline float computeTtcBasic(float distanceCm, float closingSpeedKmh) {
  float speedMs = closingSpeedKmh / 3.6f;
  if (speedMs <= 0.01f) {
    return 99.0f;
  }
  return (distanceCm / 100.0f) / speedMs;
}

/*
 * TTC Extended Formula
 * Assumes constant deceleration `a` slowing the convergence.
 * Derived from kinematic equation: d = v*t + 0.5*a*t^2
 * Reordered to quadratic: 0.5*a*t^2 - v*t + d = 0
 * t = (v - sqrt(v^2 - 2*a*d)) / a
 * For closing velocity context where v_closing is positive:
 * t = (-v_closing + sqrt(v_closing^2 + 2*a*d)) / a
 */
inline float computeTtcExtended(float distanceCm, float closingSpeedKmh, float decelMs2) {
  float distanceM = distanceCm / 100.0f;
  float speedMs = closingSpeedKmh / 3.6f;
  if (speedMs <= 0.01f) {
    return 99.0f;
  }
  
  if (decelMs2 < 0.01f) {
      return distanceM / speedMs; // fallback to basic if low decel
  }

  // discriminant = v^2 - 2 * a * d
  float discriminant = speedMs * speedMs - 2.0f * decelMs2 * distanceM;
  if (discriminant < 0.0f) {
    return 99.0f; // Stops before collision
  }
  
  // time = (v - sqrt(v^2 - 2*a*d)) / a
  return (speedMs - sqrt(discriminant)) / decelMs2;
}
