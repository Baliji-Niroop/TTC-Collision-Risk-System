#pragma once

static const unsigned long SERIAL_BAUD_RATE = 115200UL;
static const unsigned long PACKET_INTERVAL_MS = 200UL;

static const float TTC_CRITICAL_S = 1.5f;
static const float TTC_WARNING_S = 3.0f;

// --- Feature Flags ---
// 1 = Enable physical hardware. 0 = Use fallback/mock
#define USE_VL53L1X 0
#define USE_MPU6050 1
// #define ENABLE_ML_CLASSIFIER 1 // Uncomment to use trained ML model instead of physics threshold

static const float DEFAULT_DISTANCE_CM = 5000.0f;
static const float DEFAULT_SPEED_KMH = 18.0f;
static const float DEFAULT_DECEL_MS2 = 5.0f;
