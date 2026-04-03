#pragma once

#include "arduino_compat.h"

// Canonical packet contract (exact order):
// timestamp_ms,distance_cm,speed_kmh,ttc_basic,ttc_ext,risk_class,confidence\n
inline void emitTelemetryPacket(
    unsigned long timestamp_ms,
    float distance_cm,
    float speed_kmh,
    float ttc_basic,
    float ttc_ext,
    int risk_class,
    float confidence) {
  Serial.print(timestamp_ms);
  Serial.print(',');
  Serial.print(distance_cm, 2);
  Serial.print(',');
  Serial.print(speed_kmh, 2);
  Serial.print(',');
  Serial.print(ttc_basic, 2);
  Serial.print(',');
  Serial.print(ttc_ext, 2);
  Serial.print(',');
  Serial.print(risk_class);
  Serial.print(',');
  Serial.println(confidence, 2);
}
