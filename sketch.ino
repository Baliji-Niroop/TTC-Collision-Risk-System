#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define USE_MPU6050 0
#if USE_MPU6050
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#endif

static const uint8_t PIN_TRIG = 5;
static const uint8_t PIN_ECHO = 18;
static const uint8_t PIN_LED_SAFE = 25;
static const uint8_t PIN_LED_WARNING = 26;
static const uint8_t PIN_LED_CRITICAL = 27;
static const uint8_t PIN_BUZZER = 32;
static const uint8_t I2C_SDA = 21;
static const uint8_t I2C_SCL = 22;

static const float TTC_CRITICAL_SEC = 1.5f;
static const float TTC_WARNING_SEC = 3.0f;
static const float DECELERATION_MPS2 = 5.0f;
static const float VALID_DISTANCE_MIN_CM = 2.0f;
static const float VALID_DISTANCE_MAX_CM = 450.0f;
static const unsigned long SAMPLE_INTERVAL_MS = 200;
static const uint8_t HISTORY_SIZE = 6;

Adafruit_SSD1306 display(128, 64, &Wire, -1);

#if USE_MPU6050
Adafruit_MPU6050 imu;
bool imuReady = false;
#endif

float distanceHistory[HISTORY_SIZE] = {0};
uint8_t historyCount = 0;
uint8_t historyIndex = 0;

float previousDistanceCm = NAN;
unsigned long previousSampleMs = 0;

static float clampFloat(float value, float low, float high) {
  if (value < low) return low;
  if (value > high) return high;
  return value;
}

static float readDistanceCm() {
  digitalWrite(PIN_TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(PIN_TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(PIN_TRIG, LOW);

  unsigned long duration = pulseIn(PIN_ECHO, HIGH, 30000UL);
  if (duration == 0UL) {
    return NAN;
  }

  return (duration * 0.0343f) * 0.5f;
}

static float computeExtendedTtcSec(float distanceM, float speedMps) {
  if (speedMps <= 0.05f) {
    return 9999.0f;
  }

  float discriminant = (speedMps * speedMps) + (2.0f * DECELERATION_MPS2 * distanceM);
  if (discriminant < 0.0f) {
    return 9999.0f;
  }

  float ttc = (-speedMps + sqrtf(discriminant)) / DECELERATION_MPS2;
  if (!isfinite(ttc) || ttc < 0.0f) {
    return 9999.0f;
  }

  return ttc;
}

static int classifyRisk(float ttcSec) {
  if (!isfinite(ttcSec) || ttcSec > TTC_WARNING_SEC) {
    return 0;
  }
  if (ttcSec > TTC_CRITICAL_SEC) {
    return 1;
  }
  return 2;
}

static const char *riskLabel(int riskClass) {
  switch (riskClass) {
    case 1: return "WARNING";
    case 2: return "CRITICAL";
    default: return "SAFE";
  }
}

static void pushHistory(float distanceCm) {
  distanceHistory[historyIndex] = distanceCm;
  historyIndex = (historyIndex + 1) % HISTORY_SIZE;
  if (historyCount < HISTORY_SIZE) {
    historyCount++;
  }
}

static float computeConfidence(float distanceCm, float speedKmh, bool imuReadyFlag) {
  float stability = 0.75f;

  if (historyCount >= 2) {
    float totalDelta = 0.0f;
    uint8_t validPairs = historyCount - 1;
    for (uint8_t i = 1; i < historyCount; ++i) {
      uint8_t current = (historyIndex + HISTORY_SIZE - i) % HISTORY_SIZE;
      uint8_t previous = (historyIndex + HISTORY_SIZE - i - 1) % HISTORY_SIZE;
      totalDelta += fabsf(distanceHistory[current] - distanceHistory[previous]);
    }
    float meanDelta = totalDelta / validPairs;
    stability = 1.0f - clampFloat(meanDelta / 20.0f, 0.0f, 1.0f);
  }

  float motion = clampFloat(speedKmh / 60.0f, 0.0f, 1.0f);
  float confidence = 0.58f + (0.25f * stability) + (0.12f * motion);

  if (imuReadyFlag) {
    confidence += 0.03f;
  }

  if (!isfinite(distanceCm) || distanceCm < VALID_DISTANCE_MIN_CM || distanceCm > VALID_DISTANCE_MAX_CM) {
    confidence *= 0.5f;
  }

  return clampFloat(confidence, 0.05f, 0.99f);
}

static void setOutputs(int riskClass) {
  digitalWrite(PIN_LED_SAFE, riskClass == 0 ? HIGH : LOW);
  digitalWrite(PIN_LED_WARNING, riskClass == 1 ? HIGH : LOW);
  digitalWrite(PIN_LED_CRITICAL, riskClass == 2 ? HIGH : LOW);

  if (riskClass == 2) {
    tone(PIN_BUZZER, 2200);
  } else {
    noTone(PIN_BUZZER);
  }
}

static void renderDisplay(float distanceCm, float speedKmh, float ttcBasicSec, float ttcExtSec, int riskClass, float confidence) {
  display.clearDisplay();
  display.setTextColor(SSD1306_WHITE);

  display.setTextSize(1);
  display.setCursor(0, 0);
  display.print("TTC ");
  display.print(riskLabel(riskClass));

  display.setCursor(0, 14);
  display.print("D:");
  display.print(distanceCm, 1);
  display.print(" cm");

  display.setCursor(0, 26);
  display.print("V:");
  display.print(speedKmh, 1);
  display.print(" km/h");

  display.setCursor(0, 38);
  display.print("B:");
  display.print(ttcBasicSec, 2);
  display.print(" E:");
  display.print(ttcExtSec, 2);

  display.setCursor(0, 50);
  display.print("C:");
  display.print(confidence, 2);

  display.display();
}

void setup() {
  pinMode(PIN_TRIG, OUTPUT);
  pinMode(PIN_ECHO, INPUT);
  pinMode(PIN_LED_SAFE, OUTPUT);
  pinMode(PIN_LED_WARNING, OUTPUT);
  pinMode(PIN_LED_CRITICAL, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);

  digitalWrite(PIN_LED_SAFE, LOW);
  digitalWrite(PIN_LED_WARNING, LOW);
  digitalWrite(PIN_LED_CRITICAL, LOW);
  noTone(PIN_BUZZER);

  Serial.begin(115200);
  delay(200);

  Wire.begin(I2C_SDA, I2C_SCL);
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("0,0,0,0,0,2,0");
    while (true) {
      delay(1000);
    }
  }

  display.clearDisplay();
  display.display();

#if USE_MPU6050
  imuReady = imu.begin();
#endif

  previousSampleMs = millis();
}

void loop() {
  unsigned long now = millis();
  if (now - previousSampleMs < SAMPLE_INTERVAL_MS) {
    delay(5);
    return;
  }

  float elapsedSec = (now - previousSampleMs) / 1000.0f;
  previousSampleMs = now;

  float distanceCm = readDistanceCm();
  if (!isfinite(distanceCm)) {
    distanceCm = isfinite(previousDistanceCm) ? previousDistanceCm : 200.0f;
  }

  distanceCm = clampFloat(distanceCm, VALID_DISTANCE_MIN_CM, VALID_DISTANCE_MAX_CM);

  float closingSpeedMps = 0.0f;
  if (isfinite(previousDistanceCm) && elapsedSec > 0.0f) {
    float deltaCm = previousDistanceCm - distanceCm;
    if (deltaCm > 0.0f) {
      closingSpeedMps = (deltaCm / 100.0f) / elapsedSec;
    }
  }

  float speedKmh = closingSpeedMps * 3.6f;
  float distanceM = distanceCm / 100.0f;

  float ttcBasicSec = (closingSpeedMps > 0.05f) ? (distanceM / closingSpeedMps) : 9999.0f;
  float ttcExtSec = computeExtendedTtcSec(distanceM, closingSpeedMps);
  int riskClass = classifyRisk(ttcBasicSec);

#if USE_MPU6050
  bool imuReadyFlag = imuReady;
#else
  bool imuReadyFlag = false;
#endif
  float confidence = computeConfidence(distanceCm, speedKmh, imuReadyFlag);

  pushHistory(distanceCm);
  setOutputs(riskClass);
  renderDisplay(distanceCm, speedKmh, ttcBasicSec, ttcExtSec, riskClass, confidence);

  Serial.printf("%lu,%.2f,%.2f,%.2f,%.2f,%d,%.2f\n",
                now,
                distanceCm,
                speedKmh,
                ttcBasicSec,
                ttcExtSec,
                riskClass,
                confidence);

  previousDistanceCm = distanceCm;
}