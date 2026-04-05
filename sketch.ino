#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>

// ==========================================
// 1. HARDWARE PIN DEFINITIONS (Wokwi Sync)
// ==========================================
// Sonar 1
static const uint8_t PIN_TRIG_1 = 5;
static const uint8_t PIN_ECHO_1 = 18;
// Sonar 2 (Proxy for LiDAR)
static const uint8_t PIN_TRIG_2 = 4;
static const uint8_t PIN_ECHO_2 = 16;
// Encoder
static const uint8_t PIN_ENCODER_A = 19;
static const uint8_t PIN_ENCODER_B = 23;
// Outputs
static const uint8_t PIN_LED_SAFE1    = 25;
static const uint8_t PIN_LED_SAFE2    = 26;
static const uint8_t PIN_LED_WARNING1 = 27;
static const uint8_t PIN_LED_WARNING2 = 14;
static const uint8_t PIN_LED_CRITICAL = 12;
static const uint8_t PIN_BUZZER       = 32;

// ==========================================
// 2. CONFIGURATION & STATE
// ==========================================
static const unsigned long PACKET_INTERVAL_MS = 200;
static const float TTC_CRITICAL_S = 1.5f;
static const float TTC_WARNING_S = 3.0f;

Adafruit_SSD1306 display(128, 64, &Wire, -1);
Adafruit_MPU6050 imu;
bool imuReady = false;

volatile long encoderPulses = 0;
unsigned long lastEncoderTime = 0;

float currentDecelMs2 = 0.0f; 
float lastSonarDisagreement = 0.0f;
unsigned long previousSampleMs = 0;

// ==========================================
// 3. KALMAN FILTER FOR DISTANCE
// ==========================================
typedef struct {
    float x, P, Q, R, K; 
    bool initialized;
} KalmanFilter1D;

KalmanFilter1D kalmanFilter;

void kalmanInit(KalmanFilter1D* kf, float q, float r, float p) {
    kf->Q = q; kf->R = r; kf->P = p;
    kf->x = 0.0f; kf->initialized = false;
}

float kalmanUpdate(KalmanFilter1D* kf, float measurement) {
    if (!kf->initialized) {
        kf->x = measurement;
        kf->initialized = true;
        return kf->x;
    }
    kf->P += kf->Q;
    kf->K = kf->P / (kf->P + kf->R);
    kf->x = kf->x + kf->K * (measurement - kf->x);
    kf->P = (1.0f - kf->K) * kf->P;
    return kf->x;
}

// ==========================================
// 4. SENSOR READING LOGIC
// ==========================================
void IRAM_ATTR encoderISR() {
    if (digitalRead(PIN_ENCODER_B) > 0) encoderPulses++;
    else encoderPulses--;
}

float readUltrasonicBase(uint8_t trigPin, uint8_t echoPin) {
    digitalWrite(trigPin, LOW);  delayMicroseconds(2);
    digitalWrite(trigPin, HIGH); delayMicroseconds(10);
    digitalWrite(trigPin, LOW);
    unsigned long duration = pulseIn(echoPin, HIGH, 30000UL); // 30ms timeout
    if (duration == 0UL) return -1.0f;
    return (duration * 0.0343f) * 0.5f;
}

// FUSE DISTANCE: Sonar1 + Sonar2 (Sonar2 simulates VL53L1X LiDAR proxy)
float fuseDistance() {
    float s1 = readUltrasonicBase(PIN_TRIG_1, PIN_ECHO_1);
    float s2 = readUltrasonicBase(PIN_TRIG_2, PIN_ECHO_2);
    
    float fused = -1.0f;
    if (s1 > 0 && s2 > 0) {
        fused = 0.40f * s1 + 0.60f * s2;
        lastSonarDisagreement = abs(s1 - s2);
    } else if (s1 > 0) {
        fused = s1;
        lastSonarDisagreement = 50.0f; // Penalty for missing sensor
    } else if (s2 > 0) {
        fused = s2;
        lastSonarDisagreement = 50.0f; 
    } else {
        lastSonarDisagreement = 100.0f;
    }
    
    if (fused > 0) return kalmanUpdate(&kalmanFilter, fused);
    return -1.0f; // Invalid
}

float computeConfidence(float distanceCm) {
    float confidence = 0.99f;
    
    // Penalty: High sonar disagreement lowers confidence
    if (lastSonarDisagreement > 5.0f) {
        confidence -= (lastSonarDisagreement * 0.01f);
    }
    
    // Penalty: Kalman variance vs raw discrepancy
    if (abs(distanceCm - kalmanFilter.x) > 10.0f) {
        confidence -= 0.15f;
    }
    
    if (distanceCm < 10.0f || distanceCm > 400.0f) confidence -= 0.30f;
    
    if (confidence < 0.10f) return 0.10f;
    if (confidence > 0.99f) return 0.99f;
    return confidence;
}

float readHostSpeedKmh() {
    unsigned long now = millis();
    float dtSeconds = (now - lastEncoderTime) / 1000.0f;
    float hostSpeedKmh = 0;
    if (dtSeconds > 0.0f) {
        float revolutions = abs(encoderPulses) / 20.0f; // Assume 20 pulses per rev
        float distanceMeters = revolutions * 0.33f; // 0.33m circumference
        hostSpeedKmh = (distanceMeters / dtSeconds) * 3.6f;
        encoderPulses = 0;
        lastEncoderTime = now;
    }
    return hostSpeedKmh;
}

// ==========================================
// 5. TTC CALCULUS & RISK
// ==========================================
#define HIST_SIZE 3
float distHist[HIST_SIZE] = {0};
unsigned long timeHist[HIST_SIZE] = {0};
uint8_t hIdx = 0, hCount = 0;

float computeClosingSpeedKmh(float currentDistanceCm, unsigned long timestampMs) {
    distHist[hIdx] = currentDistanceCm;
    timeHist[hIdx] = timestampMs;
    hIdx = (hIdx + 1) % HIST_SIZE;
    if (hCount < HIST_SIZE) hCount++;

    if (hCount < HIST_SIZE) return 0.0f;

    uint8_t oldestIdx = hIdx;
    uint8_t newestIdx = (hIdx + HIST_SIZE - 1) % HIST_SIZE;
    
    float deltaCm = distHist[oldestIdx] - distHist[newestIdx];
    float elapsedSec = (timeHist[newestIdx] - timeHist[oldestIdx]) / 1000.0f;

    if (elapsedSec > 0.0f && deltaCm > 0.0f) { // Approaching
        return ((deltaCm / 100.0f) / elapsedSec) * 3.6f;
    }
    return 0.0f; // Receding or stationary
}

float computeTtcBasic(float distanceCm, float closingSpeedKmh) {
    float speedMs = closingSpeedKmh / 3.6f;
    if (speedMs <= 0.01f) return 99.0f;
    return (distanceCm / 100.0f) / speedMs;
}

float computeTtcExtended(float distanceCm, float closingSpeedKmh, float decelMs2) {
    float distanceM = distanceCm / 100.0f;
    float speedMs = closingSpeedKmh / 3.6f;
    if (speedMs <= 0.01f) return 99.0f;
    if (decelMs2 <= 0.01f) return distanceM / speedMs;

    // t = (v - sqrt(v^2 - 2ad)) / a
    float discriminant = speedMs * speedMs - 2.0f * decelMs2 * distanceM;
    if (discriminant < 0.0f) return 99.0f; // Will stop before hitting
    return (speedMs - sqrt(discriminant)) / decelMs2;
}

int classifyRisk(float ttcSeconds) {
    if (ttcSeconds <= TTC_CRITICAL_S) return 2;
    if (ttcSeconds <= TTC_WARNING_S) return 1;
    return 0;
}

// ==========================================
// 6. OUTPUTS (UI & Serial)
// ==========================================
void setOutputs(int riskClass) {
    static int lastRisk = -1;
    digitalWrite(PIN_LED_SAFE1, HIGH); 
    digitalWrite(PIN_LED_SAFE2, HIGH);
    
    digitalWrite(PIN_LED_WARNING1, (riskClass >= 1) ? HIGH : LOW);
    digitalWrite(PIN_LED_WARNING2, (riskClass >= 1) ? HIGH : LOW);
    
    digitalWrite(PIN_LED_CRITICAL, (riskClass >= 2) ? HIGH : LOW);
    
    if (riskClass >= 2 && lastRisk < 2) tone(PIN_BUZZER, 2200);
    else if (riskClass < 2 && lastRisk >= 2) noTone(PIN_BUZZER);
    
    lastRisk = riskClass;
}

void displayTelemetry(float dist, float spd, float ttc1, float ttc2, int risk, float conf) {
    display.clearDisplay();
    display.setTextSize(1);
    display.setCursor(0,0);
    
    display.print(F("DST: ")); display.print(dist, 1); display.println(F("cm"));
    display.print(F("SPD: ")); display.print(spd, 1);  display.println(F("kmh"));
    
    display.print(F("TTC (Basic): ")); 
    if(ttc1 >= 99.0f) display.println(F("SAFE")); else { display.print(ttc1, 2); display.println(F("s")); }
    
    display.print(F("TTC (Ext)  : ")); 
    if(ttc2 >= 99.0f) display.println(F("SAFE")); else { display.print(ttc2, 2); display.println(F("s")); }
    
    display.print(F("RISK: "));
    if (risk == 0) display.println(F("SAFE"));
    else if (risk == 1) display.println(F("WARNING "));
    else if (risk == 2) display.println(F("CRITICAL"));

    display.print(F("CONF: ")); display.print(conf * 100, 0); display.println(F("%"));
    display.display();
}

// ==========================================
// 7. SETUP & MAIN LOOP
// ==========================================
void setup() {
    Serial.begin(115200);
    delay(200);

    // Outputs
    pinMode(PIN_LED_SAFE1, OUTPUT); pinMode(PIN_LED_SAFE2, OUTPUT);
    pinMode(PIN_LED_WARNING1, OUTPUT); pinMode(PIN_LED_WARNING2, OUTPUT);
    pinMode(PIN_LED_CRITICAL, OUTPUT); pinMode(PIN_BUZZER, OUTPUT);
    setOutputs(0);

    // Pins Sensors
    pinMode(PIN_TRIG_1, OUTPUT); pinMode(PIN_ECHO_1, INPUT);
    pinMode(PIN_TRIG_2, OUTPUT); pinMode(PIN_ECHO_2, INPUT);
    pinMode(PIN_ENCODER_A, INPUT_PULLUP); pinMode(PIN_ENCODER_B, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(PIN_ENCODER_A), encoderISR, RISING);

    kalmanInit(&kalmanFilter, 0.01f, 0.5f, 1.0f);
    lastEncoderTime = millis();

    // I2C Hardware
    Wire.begin();
    if (imu.begin()) {
        imuReady = true;
        imu.setAccelerometerRange(MPU6050_RANGE_8_G);
    }
    
    if(display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
        display.clearDisplay();
        display.setTextColor(SSD1306_WHITE);
        display.setTextSize(1);
        display.setCursor(0,0);
        display.println(F("TTC SYSTEM ALIVE"));
        display.display();
    }
    
    previousSampleMs = millis();
}

void loop() {
    unsigned long now = millis();
    if (now - previousSampleMs < PACKET_INTERVAL_MS) return;
    previousSampleMs = now;

    // 1. Read Raw Distances
    float distanceCm = fuseDistance();
    if (distanceCm < 0) distanceCm = 999.0f; // Out of range
    
    // 2. Read Speed & IMU
    float hostSpeedKmh = readHostSpeedKmh();
    if (imuReady) {
        sensors_event_t a, g, temp;
        imu.getEvent(&a, &g, &temp);
        currentDecelMs2 = -a.acceleration.x; 
        if (currentDecelMs2 < 0.0f) currentDecelMs2 = 0.0f;
    }

    // 3. Compute Engine
    float closingSpeedKmh = computeClosingSpeedKmh(distanceCm, now);
    float ttcBasic = computeTtcBasic(distanceCm, closingSpeedKmh);
    float ttcExt = computeTtcExtended(distanceCm, closingSpeedKmh, currentDecelMs2);
    
    // 4. Analytics
    float confidence = computeConfidence(distanceCm);
    int risk = classifyRisk(ttcBasic);

    // 5. Outputs
    setOutputs(risk);
    displayTelemetry(distanceCm, hostSpeedKmh, ttcBasic, ttcExt, risk, confidence);

    // 6. Serial Telemetry
    Serial.printf("%lu,%.2f,%.2f,%.2f,%.2f,%d,%.2f\n",
                  now, distanceCm, hostSpeedKmh, ttcBasic, ttcExt, risk, confidence);
}