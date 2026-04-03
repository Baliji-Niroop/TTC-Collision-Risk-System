#pragma once

#include "../config/arduino_compat.h"

#include "../config/config.h"

inline float readDistanceCm() {
  static float simulatedDistance = DEFAULT_DISTANCE_CM;
  simulatedDistance -= (DEFAULT_SPEED_KMH / 3.6f) * (PACKET_INTERVAL_MS / 1000.0f) * 100.0f;
  if (simulatedDistance <= 120.0f) {
    simulatedDistance = DEFAULT_DISTANCE_CM;
  }
  return simulatedDistance;
}

inline float readSpeedKmh() {
  return DEFAULT_SPEED_KMH;
}

inline float readConfidence() {
  return 0.94f;
}
