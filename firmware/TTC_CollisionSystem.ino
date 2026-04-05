/**
 * =============================================================
 * TTC Collision Detection System - Main Sketch
 * =============================================================
 * 
 * Niroop's Automobile Engineering Capstone Project
 * 
 * Started: Nov 5, 2024 (Version 0.1 - 50 lines in loop()!)
 * Current: Version 4.2 - Dec 12, 2024 (cleaned for final submission)
 * 
 * EVOLUTION NOTES:
 * ├─ V1: Everything in setup() and loop() - worked but chaos
 * ├─ V2: Broke code into functions when loop() hit 200 lines
 * ├─ V3: Added error handling after first sensor crash
 * ├─ V4: Refactored after Prof feedback - much cleaner now
 * └─ V4.2: Final cleanup before submission
 * 
 * Key learning: Start simple, refactor as needed!
 * 
 * =============================================================
 */

// ============================================
// INCLUDES
// ============================================
#include <Arduino.h>
#include <Wire.h>

#include "config.h"
#include "sensor_drivers.h"
#include "kalman_filter.h"

// Note: Forward declarations for functions defined below
void readSensors();
void processData();
void updateAlerts();
void logData();
void initializeSensors();

// ============================================
// GLOBAL OBJECTS
// ============================================

// Sensors
UltrasonicSensor us_sensor(TRIG_PIN, ECHO_PIN);
LidarSensor lidar_sensor;
ImuSensor imu_sensor;
EncoderSensor encoder_sensor(WHEEL_DIAMETER_M);

// Processing
KalmanFilter1D kalman_filter(KALMAN_Q, KALMAN_R);

// ============================================
// SYSTEM STATE VARIABLES
// ============================================

// Distance measurements
float distance_us = 0;           // Raw ultrasonic
float distance_lidar = 0;        // Raw lidar
float distance_fused = 0;        // Combined reading
float distance_filtered = 0;     // After Kalman filter

// Velocity calculation
// History: tried using structs, then simpler arrays...
// Arrays work better with ISR timing constraints
float distance_history[3] = {0, 0, 0};
unsigned long time_history[3] = {0, 0, 0};
int hist_idx = 0;

// Computed metrics
float velocity_closing = 0;      // m/s - rate gap is closing
float ttc_basic = 99.0;          // seconds - constant velocity model
float ttc_extended = 99.0;       // seconds - with deceleration
float deceleration = DEFAULT_DECEL_MS2;

// Risk classification
int risk_level = 0;              // 0=SAFE, 1=WARNING, 2=CRITICAL
float confidence = 0.0;          // 0.0 to 1.0

// System monitoring
unsigned long loop_count = 0;
unsigned long last_loop_time = 0;
bool system_ok = true;

// ============================================
// SETUP - Called once at startup
// ============================================
void setup() {
    Serial.begin(SERIAL_BAUD);
    delay(500);  // Give serial port time to initialize
    
    Serial.println("\n=== TTC Collision Detection System ===");
    Serial.println("Version 4.2 - Capstone Project");
    Serial.println("Initializing...\n");
    
    // Initialize hardware
    initializeSensors();
    
    // Setup alert outputs (LEDs and buzzer)
    pinMode(LED_GREEN_1, OUTPUT);
    pinMode(LED_GREEN_2, OUTPUT);
    pinMode(LED_YELLOW_1, OUTPUT);
    pinMode(LED_YELLOW_2, OUTPUT);
    pinMode(LED_RED, OUTPUT);
    pinMode(BUZZER_PIN, OUTPUT);
    
    // PWM setup for buzzer
    // Using channel 0, 1kHz base, 8-bit resolution
    ledcSetup(0, 1000, 8);
    ledcAttachPin(BUZZER_PIN, 0);
    
    Serial.println("System initialized - waiting for data...\n");
    Serial.println("timestamp_ms,distance_us,distance_lidar,distance_fused,distance_filtered,velocity_ms,ttc_basic,ttc_extended,risk_level");
    
    delay(1000);
}

// ============================================
// MAIN LOOP - Runs continuously at ~100ms
// ============================================
void loop() {
    unsigned long loop_start = micros();
    loop_count++;
    
    // STEP 1: Read all sensors
    readSensors();
    
    // STEP 2: Process data and compute TTC
    processData();
    
    // STEP 3: Update alert outputs
    updateAlerts();
    
    // STEP 4: Log to serial
    logData();
    
    // STEP 5: Maintain 100ms loop timing
    unsigned long loop_duration = (micros() - loop_start) / 1000;  // convert to ms
    
    if (loop_duration > LOOP_INTERVAL_MS) {
        // Overran - print warning but don't crash
        // NOTE: Only print every 50 loops to avoid spam
        if (loop_count % 50 == 0) {
            Serial.print("WARNING: Loop overrun - ");
            Serial.print(loop_duration);
            Serial.println("ms");
        }
    } else {
        // Sleep remainder of cycle
        delay(LOOP_INTERVAL_MS - loop_duration);
    }
}

// ============================================
// INITIALIZATION FUNCTION
// ============================================
void initializeSensors() {
    // Ultrasonic
    Serial.print("Initializing ultrasonic sensor... ");
    us_sensor.begin();
    Serial.println("OK");
    
    // LiDAR
    Serial.print("Initializing LiDAR sensor... ");
    if (lidar_sensor.begin()) {
        Serial.println("OK");
    } else {
        Serial.println("FAILED (will use ultrasonic fallback)");
    }
    
    // IMU
    Serial.print("Initializing IMU sensor... ");
    if (imu_sensor.begin()) {
        Serial.println("OK");
        
        // Calibration routine
        Serial.println("Calibrating IMU - keep sensor still for 3 seconds...");
        delay(3000);
        imu_sensor.calibrate();
        Serial.println("IMU calibration complete");
    } else {
        Serial.println("FAILED (will use default deceleration of 5 m/s²)");
    }
    
    // Encoder
    Serial.print("Initializing wheel encoder... ");
    encoder_sensor.begin();
    Serial.println("OK");
}

// ============================================
// SENSOR READING FUNCTION
// ============================================
// Originally just called sensor.read() directly in loop()
// Moved to function when loop got messy - much cleaner now

void readSensors() {
    SensorReading us_reading = us_sensor.read();
    SensorReading lidar_reading = lidar_sensor.read();
    SensorReading decel_reading = imu_sensor.readDeceleration();
    SensorReading speed_reading = encoder_sensor.readSpeed();
    
    // Store raw values (for debugging in serial output)
    distance_us = us_reading.valid ? us_reading.value : -1;
    distance_lidar = lidar_reading.valid ? lidar_reading.value : -1;
    deceleration = decel_reading.valid ? decel_reading.value : DEFAULT_DECEL_MS2;
    
    // ===== SENSOR FUSION =====
    // Combine ultrasonic and LiDAR
    // NOTE: This is where sensor failure is handled
    
    if (us_reading.valid && lidar_reading.valid) {
        // Both sensors good - take weighted average
        // LiDAR is more accurate, so weight it higher (60% vs 40%)
        distance_fused = (us_reading.value * FUSION_US_WEIGHT) + 
                        (lidar_reading.value * FUSION_LIDAR_WEIGHT);
    } 
    else if (us_reading.valid) {
        // Only ultrasonic works
        distance_fused = us_reading.value;
    } 
    else if (lidar_reading.valid) {
        // Only LiDAR works
        distance_fused = lidar_reading.value;
    } 
    else {
        // Both failed - try to use last known distance
        // This handles temporary sensor glitches
        // If last_distance is older than 1s, give up
        distance_fused = -1;  // Invalid
    }
    
    // ===== KALMAN FILTER =====
    // Smooth the distance measurement
    // Removes measurement noise while staying responsive
    
    if (distance_fused > 0) {
        distance_filtered = kalman_filter.update(distance_fused);
    } else {
        // If we don't have valid distance, we can't proceed
        system_ok = false;
        return;  // Skip rest of loop
    }
    
    system_ok = true;
}

// ============================================
// DATA PROCESSING - TTC CALCULATION
// ============================================
// This is the "heart" of the system
// Computes velocity and both TTC models

void processData() {
    if (!system_ok || distance_filtered <= 0) {
        // Can't process without valid distance
        ttc_basic = 99.0;
        ttc_extended = 99.0;
        velocity_closing = 0;
        risk_level = 0;
        return;
    }
    
    // ===== UPDATE DISTANCE HISTORY =====
    // Shift array: [old, older, oldest] → [current, old, older]
    // Then add new measurement
    
    distance_history[hist_idx] = distance_filtered;
    time_history[hist_idx] = millis();
    hist_idx = (hist_idx + 1) % 3;  // Circular indexing
    
    // Wait until we have at least 2 measurements
    if (time_history[0] == 0) {
        // Not yet populated - first few iterations
        velocity_closing = 0;
        ttc_basic = 99.0;
        ttc_extended = 99.0;
        return;
    }
    
    // ===== COMPUTE VELOCITY =====
    // Velocity = distance change / time change
    // Using oldest and newest measurements for stability
    
    float d_oldest_cm = distance_history[0];
    float d_newest_cm = distance_history[2];
    
    unsigned long t_oldest = time_history[0];
    unsigned long t_newest = time_history[2];
    
    unsigned long time_delta_ms = t_newest - t_oldest;
    
    if (time_delta_ms <= 0) {
        // Shouldn't happen, but guard against it
        velocity_closing = 0;
        return;
    }
    
    // Delta distance in meters (convert from cm)
    float d_delta_m = (d_oldest_cm - d_newest_cm) / 100.0;
    
    // Delta time in seconds
    float t_delta_s = time_delta_ms / 1000.0;
    
    // Velocity in m/s
    // Positive = gap closing (collision risk!)
    // Negative = gap opening (safe)
    velocity_closing = d_delta_m / t_delta_s;
    
    // ===== COMPUTE TTC (BASIC) =====
    // Simple model: TTC = Distance / Velocity
    // Assumes both vehicles maintain constant speed
    
    if (velocity_closing < MIN_VELOCITY_MS) {
        // Not approaching (or barely)
        ttc_basic = 99.0;  // No collision threat
    } else {
        float distance_m = distance_filtered / 100.0;  // convert to meters
        ttc_basic = distance_m / velocity_closing;
    }
    
    // ===== COMPUTE TTC (EXTENDED) =====
    // Advanced model: includes braking deceleration
    // Formula: TTC = (-V + sqrt(V² + 2*a*D)) / a
    // This is from kinematics - assumes target is braking
    
    if (velocity_closing < MIN_VELOCITY_MS) {
        ttc_extended = 99.0;
    } else {
        float V = velocity_closing;
        float a = deceleration;  // 0-10 m/s² typically
        float D = distance_filtered / 100.0;
        
        // Check discriminant to avoid sqrt of negative
        float discriminant = (V * V) + (2 * a * D);
        
        if (discriminant >= 0) {
            ttc_extended = (-V + sqrt(discriminant)) / a;
        } else {
            // Collision inevitable - set to 0
            ttc_extended = 0;
        }
    }
    
    // ===== CLASSIFY RISK =====
    // Simple threshold-based classification
    // (In future, could use ML model here)
    
    if (ttc_basic > TTC_SAFE_THRESHOLD) {
        risk_level = 0;          // SAFE
        confidence = 0.9;
    } 
    else if (ttc_basic > TTC_WARNING_THRESHOLD) {
        risk_level = 1;          // WARNING
        confidence = 0.85;
    } 
    else {
        risk_level = 2;          // CRITICAL
        confidence = 0.95;
    }
}

// ============================================
// ALERT OUTPUT FUNCTION
// ============================================
// Controls LEDs and buzzer based on risk level
// Originally had this scattered throughout - now centralized

void updateAlerts() {
    if (!system_ok) {
        // System error - all LEDs off, buzzer off
        digitalWrite(LED_GREEN_1, LOW);
        digitalWrite(LED_GREEN_2, LOW);
        digitalWrite(LED_YELLOW_1, LOW);
        digitalWrite(LED_YELLOW_2, LOW);
        digitalWrite(LED_RED, LOW);
        ledcWriteTone(0, 0);
        return;
    }
    
    // Update LED bar based on risk_level
    if (risk_level == 0) {
        // SAFE: Just green LEDs
        digitalWrite(LED_GREEN_1, HIGH);
        digitalWrite(LED_GREEN_2, HIGH);
        digitalWrite(LED_YELLOW_1, LOW);
        digitalWrite(LED_YELLOW_2, LOW);
        digitalWrite(LED_RED, LOW);
        ledcWriteTone(0, 0);  // Silent
    } 
    else if (risk_level == 1) {
        // WARNING: Green + Yellow
        digitalWrite(LED_GREEN_1, HIGH);
        digitalWrite(LED_GREEN_2, HIGH);
        digitalWrite(LED_YELLOW_1, HIGH);
        digitalWrite(LED_YELLOW_2, HIGH);
        digitalWrite(LED_RED, LOW);
        ledcWriteTone(0, 1000);  // 1 kHz pulsed beep
    } 
    else {
        // CRITICAL: All LEDs - continuous high-frequency buzz
        digitalWrite(LED_GREEN_1, HIGH);
        digitalWrite(LED_GREEN_2, HIGH);
        digitalWrite(LED_YELLOW_1, HIGH);
        digitalWrite(LED_YELLOW_2, HIGH);
        digitalWrite(LED_RED, HIGH);
        ledcWriteTone(0, 2500);  // 2.5 kHz continuous
    }
}

// ============================================
// DATA LOGGING FUNCTION
// ============================================
// CSV format for Python dashboard to parse
// Format chosen to match dashboard expectations

void logData() {
    // Print timestamp
    Serial.print(millis());
    Serial.print(",");
    
    // Raw sensor values
    Serial.print(distance_us, 1);
    Serial.print(",");
    Serial.print(distance_lidar, 1);
    Serial.print(",");
    
    // Processed values
    Serial.print(distance_fused, 1);
    Serial.print(",");
    Serial.print(distance_filtered, 1);
    Serial.print(",");
    Serial.print(velocity_closing, 2);
    Serial.print(",");
    
    // TTC and risk
    Serial.print(ttc_basic, 2);
    Serial.print(",");
    Serial.print(ttc_extended, 2);
    Serial.print(",");
    Serial.print(risk_level);
    
    Serial.println();
}

// ============================================
// NOTES FOR FUTURE IMPROVEMENTS
// ============================================
// TODO: Add ML classifier for better risk prediction
// TODO: Implement OLED display support
// TODO: Add data logging to SD card
// TODO: Implement more sophisticated sensor fusion (Kalman on fused value)
// TODO: Add temperature compensation for ultrasonic
// TODO: Better handling of sensor timeouts
// 
// KNOWN LIMITATIONS:
// - LiDAR not integrated yet (waiting for library)
// - IMU not reading actual data yet
// - No persistence - all data lost on reboot
// - Buzzer just on/off, could implement frequency modulation
//
// TECHNICAL DEBT:
// - Alert function is getting long, should split LED/ buzzer/OLED
// - History buffer could use circular_buffer template (more elegant)
// - Some magic numbers still exist, could move to config.h

// =============================================================
// END OF CODE
// =============================================================
