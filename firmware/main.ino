#include "config/config.h"
#include "pinmap.h"
#include "sensors/sensors.h"
#include "ml/ttc_engine.h"
#include "alerts/risk_classifier.h"
#include "ml_classifier/ml_classifier.h"

#if USE_MPU6050
#include <Adafruit_MPU6050.h>
Adafruit_MPU6050 imu;
bool imuReady = false;
#endif

// ============================================
// STATE MANAGEMENT
// ============================================
float currentDecelMs2 = DEFAULT_DECEL_MS2;
unsigned long previousSampleMs = 0;

// Encoder state (defined here, declared as extern in sensors.h)
volatile long encoderPulses = 0;
unsigned long lastEncoderTime = 0;

// ============================================
// OUTPUT CONTROL (LED + BUZZER)
// ============================================

/**
 * Clear all outputs to safe state (all LEDs off, buzzer silent)
 */
void clearOutputs() {
  digitalWrite(PIN_LED_SAFE1, LOW);
  digitalWrite(PIN_LED_SAFE2, LOW);
  digitalWrite(PIN_LED_WARNING1, LOW);
  digitalWrite(PIN_LED_WARNING2, LOW);
  digitalWrite(PIN_LED_CRITICAL, LOW);
  noTone(PIN_BUZZER);
}

/**
 * Set outputs based on risk classification
 * riskClass: 0=SAFE, 1=WARNING, 2=CRITICAL
 */
void setOutputs(int riskClass) {
  clearOutputs();

  if (riskClass == 0) {
    // SAFE - both green LEDs
    digitalWrite(PIN_LED_SAFE1, HIGH);
    digitalWrite(PIN_LED_SAFE2, HIGH);
  } else if (riskClass == 1) {
    // WARNING - both yellow LEDs
    digitalWrite(PIN_LED_WARNING1, HIGH);
    digitalWrite(PIN_LED_WARNING2, HIGH);
  } else if (riskClass == 2) {
    // CRITICAL - red LED + buzzer alarm
    digitalWrite(PIN_LED_CRITICAL, HIGH);
    tone(PIN_BUZZER, 2200);
  }
}

/**
 * Initialize all output pins as OUTPUT mode
 */
void initOutputPins() {
  for (uint8_t i = 0; i < NUM_LED_PINS; i++) {
    pinMode(LED_PINS[i], OUTPUT);
  }
  pinMode(PIN_BUZZER, OUTPUT);
  clearOutputs();
}

// ============================================
// SENSOR INITIALIZATION
// ============================================

/**
 * Initialize IMU (MPU6050) if enabled
 * Reads accelerometer to measure deceleration
 */
void initImuIfEnabled() {
#if USE_MPU6050
  if (imu.begin()) {
    imuReady = true;
    imu.setAccelerometerRange(MPU6050_RANGE_8_G);
  }
#endif
}

/**
 * Update deceleration estimate from IMU
 * Reads X-axis acceleration (represents braking)
 */
void updateDecelerationFromImu() {
#if USE_MPU6050
  if (imuReady) {
    sensors_event_t a, g, temp;
    imu.getEvent(&a, &g, &temp);
    currentDecelMs2 = -a.acceleration.x;
    if (currentDecelMs2 < 0.1f) {
      currentDecelMs2 = 0.1f;
    }
  }
#endif
}

// ============================================
// SAMPLING CONTROL
// ============================================

/**
 * Check if enough time has passed for next sensor sample
 * Implements fixed-rate sampling based on PACKET_INTERVAL_MS
 */
bool sampleDue(unsigned long nowMs) {
  if (nowMs - previousSampleMs < PACKET_INTERVAL_MS) {
    return false;
  }
  previousSampleMs = nowMs;
  return true;
}

// ============================================
// TELEMETRY EMISSION
// ============================================

/**
 * Emit canonical 7-field telemetry packet
 * Format: timestamp_ms,distance_cm,speed_kmh,ttc_basic,ttc_ext,risk_class,confidence
 * 
 * This output is consumed by:
 *   - Wokwi bridge (wokwi_serial_bridge.py) for validation
 *   - Dashboard (src/dashboard.py) for visualization
 *   - Validation suite (validation/protocol_contract_test.py)
 */
void emitTelemetryPacket(
  unsigned long nowMs,
  float distanceCm,
  float hostSpeedKmh,
  float ttcBasic,
  float ttcExt,
  int finalRisk,
  float confidence
) {
  Serial.printf("%lu,%.2f,%.2f,%.2f,%.2f,%d,%.2f\n",
                nowMs,
                distanceCm,
                hostSpeedKmh,
                ttcBasic,
                ttcExt,
                finalRisk,
                confidence);
}

// ============================================
// INITIALIZATION
// ============================================

void setup() {
  Serial.begin(115200);
  delay(200);

  initOutputPins();
  initSensors();
  initImuIfEnabled();

  previousSampleMs = millis();
}

// ============================================
// MAIN LOOP
// ============================================

/**
 * Main event loop - runs at PACKET_INTERVAL_MS cadence
 * 
 * Flow:
 *   1. Read distance from sensor fusion (sonar + optional LIDAR)
 *   2. Measure host speed from wheel encoder
 *   3. Update deceleration estimate from IMU
 *   4. Compute TTC using both basic and extended methods
 *   5. Apply optional ML classification if available
 *   6. Finalize risk class and set outputs
 *   7. Emit telemetry for logging
 */
void loop() {
  unsigned long now = millis();
  
  // Guard: only emit telemetry at fixed intervals
  if (!sampleDue(now)) {
    delay(5);
    return;
  }

  // Sensor reads
  float distanceCm = readDistanceCm(now);
  float hostSpeedKmh = readHostSpeedKmh();
  float confidence = computeConfidence(distanceCm);

  // Optional IMU update
  updateDecelerationFromImu();

  // TTC calculations
  float closingSpeedKmh = computeClosingSpeedKmh(distanceCm, now);
  float ttcBasic = computeTtcBasic(distanceCm, closingSpeedKmh);
  float ttcExt = computeTtcExtended(distanceCm, closingSpeedKmh, currentDecelMs2);

  // Risk classification
  int roadCondition = 0;
  int mlRisk = 0;

#ifdef ENABLE_ML_CLASSIFIER
  mlRisk = classifyRiskML(
    ttcBasic, ttcExt, 
    hostSpeedKmh / 3.6f,  // convert km/h to m/s
    closingSpeedKmh / 3.6f,
    currentDecelMs2,
    (float)roadCondition
  );
#endif

  int finalRisk = classifyRiskFinal(ttcBasic, roadCondition, mlRisk);

  // Actuation
  setOutputs(finalRisk);
  emitTelemetryPacket(now, distanceCm, hostSpeedKmh, ttcBasic, ttcExt, finalRisk, confidence);
}
