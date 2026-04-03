#include "config.h"
#include "sensors.h"
#include "ttc_engine.h"
#include "risk_classifier.h"
#include "serial_protocol.h"
#include "oled_display.h"

void setup() {
  Serial.begin(SERIAL_BAUD_RATE);
  displayStartupBanner();
}

void loop() {
  const unsigned long timestampMs = millis();
  const float distanceCm = readDistanceCm();
  const float speedKmh = readSpeedKmh();
  const float ttcBasic = computeTtcBasic(distanceCm, speedKmh);
  const float ttcExt = computeTtcExtended(distanceCm, speedKmh, DEFAULT_DECEL_MS2);
  const int riskClass = classifyRisk(ttcBasic);
  const float confidence = readConfidence();

  emitTelemetryPacket(timestampMs, distanceCm, speedKmh, ttcBasic, ttcExt, riskClass, confidence);
  displayTelemetry(timestampMs, distanceCm, speedKmh, ttcBasic, ttcExt, riskClass, confidence);

  delay(PACKET_INTERVAL_MS);
}
