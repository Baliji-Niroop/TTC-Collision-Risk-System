#pragma once

#include <math.h>

inline float computeTtcBasic(float distanceCm, float speedKmh) {
  float speedMs = speedKmh / 3.6f;
  if (speedMs <= 0.01f) {
    return 99.0f;
  }
  return (distanceCm / 100.0f) / speedMs;
}

inline float computeTtcExtended(float distanceCm, float speedKmh, float decelMs2) {
  float distanceM = distanceCm / 100.0f;
  float speedMs = speedKmh / 3.6f;
  if (speedMs <= 0.01f) {
    return 99.0f;
  }
  float discriminant = speedMs * speedMs + 2.0f * decelMs2 * distanceM;
  if (discriminant < 0.0f) {
    return 99.0f;
  }
  return (-speedMs + sqrt(discriminant)) / decelMs2;
}
