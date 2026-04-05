#include "config/config.h"
#include "sensors/sensors.h"
#include "ml/ttc_engine.h"
#include "alerts/risk_classifier.h"
#include "ml_classifier/ml_classifier.h"

// Hardware Pin Definitions (matching diagram.json)
static const uint8_t PIN_LED_SAFE1    = 25;
static const uint8_t PIN_LED_SAFE2    = 26;
static const uint8_t PIN_LED_WARNING1 = 27;
static const uint8_t PIN_LED_WARNING2 = 14;
static const uint8_t PIN_LED_CRITICAL = 12;
static const uint8_t PIN_BUZZER       = 32;

#if USE_MPU6050
#include <Adafruit_MPU6050.h>
Adafruit_MPU6050 imu;
bool imuReady = false;
#endif

float currentDecelMs2 = DEFAULT_DECEL_MS2;
unsigned long previousSampleMs = 0;

void setOutputs(int riskClass) {
  // Turn everything off first
  digitalWrite(PIN_LED_SAFE1, LOW);
  digitalWrite(PIN_LED_SAFE2, LOW);
  digitalWrite(PIN_LED_WARNING1, LOW);
  digitalWrite(PIN_LED_WARNING2, LOW);
  digitalWrite(PIN_LED_CRITICAL, LOW);
  noTone(PIN_BUZZER);

  if (riskClass == 0) {
    digitalWrite(PIN_LED_SAFE1, HIGH);
    digitalWrite(PIN_LED_SAFE2, HIGH);
  } else if (riskClass == 1) {
    digitalWrite(PIN_LED_WARNING1, HIGH);
    digitalWrite(PIN_LED_WARNING2, HIGH);
  } else if (riskClass == 2) {
    digitalWrite(PIN_LED_CRITICAL, HIGH);
    tone(PIN_BUZZER, 2200);
  }
}

void setup() {
  Serial.begin(115200);
  delay(200);

  // 1. Initialize output pins
  pinMode(PIN_LED_SAFE1, OUTPUT);
  pinMode(PIN_LED_SAFE2, OUTPUT);
  pinMode(PIN_LED_WARNING1, OUTPUT);
  pinMode(PIN_LED_WARNING2, OUTPUT);
  pinMode(PIN_LED_CRITICAL, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  setOutputs(0);

  // 2. Initialize sensors
  initSensors();

  // 3. Initialize IMU (if enabled)
#if USE_MPU6050
  if (imu.begin()) {
    imuReady = true;
    imu.setAccelerometerRange(MPU6050_RANGE_8_G);
  }
#endif

  previousSampleMs = millis();
}

void loop() {
  // 1. Enforce packet interval
  unsigned long now = millis();
  if (now - previousSampleMs < PACKET_INTERVAL_MS) {
    delay(5);
    return;
  }
  previousSampleMs = now;

  // 2. Read sensors
  float distanceCm = readDistanceCm(now);
  float hostSpeedKmh = readHostSpeedKmh();
  float confidence = computeConfidence(distanceCm);

  // 3. IMU Deceleration Override
#if USE_MPU6050
  if (imuReady) {
    sensors_event_t a, g, temp;
    imu.getEvent(&a, &g, &temp);
    currentDecelMs2 = -a.acceleration.x; 
    if (currentDecelMs2 < 0.1f) currentDecelMs2 = 0.1f;
  }
#endif

  // 4. Compute kinematics (TTC variants + virtual closing speed)
  float closingSpeedKmh = computeClosingSpeedKmh(distanceCm, now);
  float ttcBasic = computeTtcBasic(distanceCm, closingSpeedKmh);
  float ttcExt = computeTtcExtended(distanceCm, closingSpeedKmh, currentDecelMs2);

  // 5. Compute Risk
  int roadCondition = 0; // Constant here, could be extended via CAN or sensors
  int mlRisk = 0;
  
#ifdef ENABLE_ML_CLASSIFIER
  mlRisk = classifyRiskML(ttcBasic, ttcExt, hostSpeedKmh / 3.6f, closingSpeedKmh / 3.6f, currentDecelMs2, (float)roadCondition);
#endif

  int finalRisk = classifyRiskFinal(ttcBasic, roadCondition, mlRisk);

  // 6. Actuate User Interface outputs
  setOutputs(finalRisk);

  // 7. Emit Canonical Telemetry Packet
  Serial.printf("%lu,%.2f,%.2f,%.2f,%.2f,%d,%.2f\n",
                now,
                distanceCm,
                hostSpeedKmh,
                ttcBasic,
                ttcExt,
                finalRisk,
                confidence);
}
