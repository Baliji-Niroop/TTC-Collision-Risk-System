#ifndef SENSOR_DRIVERS_H
#define SENSOR_DRIVERS_H

/**
 * sensor_drivers.h - Hardware Abstraction Layer
 * 
 * Niroop - Automobile Engineering Capstone Project
 * Started: Nov 10, 2024
 * Last major update: Dec 5, 2024
 * 
 * Each sensor returns a SensorReading struct to make code cleaner.
 * Added the 'valid' flag after Week 1 - originally wasn't checking if readings
 * were actually good, just caused weird crashes with garbage data.
 */

#include "config.h"
#include "config/arduino_compat.h"
#include <cmath>

// ============================================
// SENSOR READING STRUCT
// ============================================
// Created this after initial mess of trying to track (value, is_valid, time)
// separately. Much cleaner to bundle them together.

struct SensorReading {
    float value;              // The measurement (distance, speed, acceleration, etc)
    bool valid;               // Within valid range?
    unsigned long timestamp;  // When we read it (millis())
    
    SensorReading() : value(0), valid(false), timestamp(0) {}
    SensorReading(float v, bool ok) : value(v), valid(ok), timestamp(millis()) {}
    SensorReading(float v, bool ok, unsigned long t) : value(v), valid(ok), timestamp(t) {}
};

// ============================================
// ULTRASONIC SENSOR (HC-SR04)
// ============================================
// First sensor I got working - pretty straightforward
// Just trigger a pulse, time the echo, convert to distance

class UltrasonicSensor {
private:
    int trig_pin;
    int echo_pin;
    
public:
    UltrasonicSensor(int trig, int echo) : trig_pin(trig), echo_pin(echo) {}
    
    void begin() {
        pinMode(trig_pin, OUTPUT);
        pinMode(echo_pin, INPUT);
        digitalWrite(trig_pin, LOW);  // Start low
    }
    
    SensorReading read() {
        // Send 10 microsecond trigger pulse
        // (HC-SR04 datasheet specifies this timing)
        digitalWrite(trig_pin, LOW);
        delayMicroseconds(2);
        digitalWrite(trig_pin, HIGH);
        delayMicroseconds(10);
        digitalWrite(trig_pin, LOW);
        
        // Wait for echo to return
        // Using 30ms timeout - anything longer is probably error or out of range
        long duration = pulseIn(echo_pin, HIGH, US_TIMEOUT_MS * 1000);
        
        // If we timeout, pulseIn returns 0
        if (duration == 0) {
            return SensorReading(0, false);
        }
        
        // Distance calculation
        // Time = 2 * distance / speed_of_sound
        //   (factor of 2 because sound goes out AND back)
        // Therefore: distance = (time * speed_of_sound) / 2
        // Speed = 0.0343 cm/microsecond
        float distance = (duration * SOUND_SPEED) / 2.0;
        
        // Sanity check - HC-SR04 specs: 2cm to 400cm
        bool valid = (distance >= US_MIN_RANGE_CM && distance <= US_MAX_RANGE_CM);
        
        return SensorReading(distance, valid);
    }
};

// ============================================
// LIDAR SENSOR (VL53L1X)
// ============================================
// Much trickier than ultrasonic. Needed to:
// 1. Learn I2C protocol
// 2. Find the right library (tried 3 different ones)
// 3. Debug address conflicts with MPU6050
//
// Professor gave me Pololu library example - helped a ton!
// Key lesson: I2C devices must have unique addresses
// VL53L1X: 0x29
// MPU6050: 0x68
// (Initially thought they were conflicting - actually was just bad soldering!)

class LidarSensor {
private:
    bool is_initialized;
    // NOTE: Using Pololu VL53L1X library
    // Would normally define sensor object here but keeping it simple for now
    // Full implementation would use: VL53L1X sensor; 
    
public:
    LidarSensor() : is_initialized(false) {}
    
    bool begin() {
        // Initialize I2C
        Wire.begin(SDA_PIN, SCL_PIN);
        Wire.setClock(400000);  // 400 kHz (I want it fast but stable)
        
        // TODO: Actual library integration needed
        // For now, returning false to trigger fallback to ultrasonic
        // Will implement when I get the full Pololu lib set up
        
        is_initialized = false;
        return false;
    }
    
    SensorReading read() {
        if (!is_initialized) {
            return SensorReading(0, false);
        }
        
        // TODO: Read actual distance from sensor
        // Would be something like:
        // uint16_t distance_mm = sensor.read();
        // float distance_cm = distance_mm / 10.0;
        
        return SensorReading(0, false);
    }
};

// ============================================
// IMU SENSOR (MPU6050)
// ============================================
// For measuring deceleration (braking acceleration)
// The trick: need to filter out gravity for Z-axis
//
// MPU6050 setup:
// - 6 DOF (accelerometer + gyroscope)
// - Accelerometer: I'm using ±2g range = 16384 units per g
// - Gyroscope: not using yet but available
//
// Calibration: First thing at startup, measure when sitting still
// This gives us the "zero offset" to subtract from all future readings

class ImuSensor {
private:
    bool is_initialized;
    int16_t accel_z_offset;  // Calibration value to subtract
    
public:
    ImuSensor() : is_initialized(false), accel_z_offset(0) {}
    
    bool begin() {
        // Initialize I2C (shared with LiDAR)
        Wire.begin(SDA_PIN, SCL_PIN);  
        
        // TODO: MPU6050 library initialization
        // Same situation as LiDAR - placeholder for now
        
        is_initialized = false;
        return false;
    }
    
    void calibrate() {
        // Called at startup - sensor must be sitting flat and still
        // Take multiple readings and average them
        // This offset gets subtracted from all future readings
        
        // TODO: Implement calibration routine
        // Would read 500 samples and average the Z acceleration
    }
    
    SensorReading readDeceleration() {
        if (!is_initialized) {
            // If IMU not working, use default deceleration
            return SensorReading(DEFAULT_DECEL_MS2, false);
        }
        
        // TODO: Read actual acceleration from sensor
        // Formula would be:
        // 1. Get raw Z-axis value
        // 2. Subtract offset (from calibration)
        // 3. Divide by 16384 to get g's
        // 4. Multiply by 9.81 to get m/s²
        // 5. Clamp to 0-15 m/s²
        
        return SensorReading(DEFAULT_DECEL_MS2, false);
    }
};

// ============================================
// ENCODER SENSOR (Wheel Speed)
// ============================================
// Most complex part was understanding interrupts!
// Encoder has 600 pulses per revolution
// Count pulses in fixed time interval to get RPM → speed
//
// Critical part: ISR (Interrupt Service Routine) must be static
// and VERY fast - can't do Serial.print() inside ISR!
// Learned this the hard way - system would hang.

class EncoderSensor {
private:
    static volatile unsigned long pulse_count;  // incremented by ISR
    static unsigned long last_read_time;
    float wheel_diameter;  // in meters
    
    // Static ISR - called when pulse detected
    // IRAM_ATTR = put in instruction RAM for faster execution
    // volatile = compiler won't optimize it away
    static void IRAM_ATTR handlePulse() {
        pulse_count++;
    }
    
public:
    EncoderSensor(float wheel_diam = WHEEL_DIAMETER_M) 
        : wheel_diameter(wheel_diam) {}
    
    void begin() {
        pinMode(ENC_CH_A, INPUT_PULLUP);
        pinMode(ENC_CH_B, INPUT_PULLUP);
        
        pulse_count = 0;
        last_read_time = millis();
        
        // Attach interrupt to channel A, trigger on rising edge
        // digitalPinToInterrupt() converts GPIO number to interrupt number
        attachInterrupt(digitalPinToInterrupt(ENC_CH_A), handlePulse, RISING);
    }
    
    SensorReading readSpeed() {
        unsigned long current_time = millis();
        unsigned long elapsed_ms = current_time - last_read_time;
        
        // Need at least 100ms for reliable reading
        // Less time = too noisy
        if (elapsed_ms < 100) {
            return SensorReading(0, false);
        }
        
        // Read pulse count safely (disable interrupts while reading)
        // ISR might try to increment while we're reading...
        // this is a race condition! Must protect with noInterrupts()
        noInterrupts();
        unsigned long pulses = pulse_count;
        pulse_count = 0;  // reset counter
        interrupts();
        
        // Calculate speed:
        // pulses / PPR = number of wheel rotations
        // rotations × circumference = distance traveled
        // distance / time = speed
        
        float rotations = pulses / (float)ENCODER_PPR;
        float circumference = 3.14159265 * wheel_diameter;
        float distance_m = rotations * circumference;
        float elapsed_s = elapsed_ms / 1000.0;
        
        // Speed in km/h (need to multiply m/s by 3.6)
        float speed_ms = distance_m / elapsed_s;
        float speed_kmh = speed_ms * 3.6;
        
        last_read_time = current_time;
        
        // Sanity check: should be between 0 and ~200 km/h
        bool valid = (speed_kmh >= 0 && speed_kmh <= 200);
        
        return SensorReading(speed_kmh, valid);
    }
};

// These MUST be defined outside the class - C++ requires this
// Spent 30 min debugging linker error before understanding...
volatile unsigned long EncoderSensor::pulse_count = 0;
unsigned long EncoderSensor::last_read_time = 0;

#endif // SENSOR_DRIVERS_H
