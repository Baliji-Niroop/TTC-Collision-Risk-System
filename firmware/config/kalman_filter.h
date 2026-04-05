#pragma once

// kalman_filter.h
// 1-D Kalman Filter implementation for noise suppression on distance measurements.

typedef struct {
    float x; // State: estimated distance
    float P; // Covariance estimate: current uncertainty
    float Q; // Process noise: expected variability in the true state 
    float R; // Measurement noise: expected sensor noise
    float K; // Kalman gain: weight applied to the new measurement
    bool initialized;
} KalmanFilter1D;

inline void kalmanInit(KalmanFilter1D* kf, float processNoise = 0.01f, float measurementNoise = 0.5f, float initialError = 1.0f) {
    kf->Q = processNoise;
    kf->R = measurementNoise;
    kf->P = initialError;
    kf->x = 0.0f;
    kf->initialized = false;
}

inline float kalmanUpdate(KalmanFilter1D* kf, float measurement) {
    if (!kf->initialized) {
        kf->x = measurement;
        kf->initialized = true;
        return kf->x;
    }

    // Prediction Update
    kf->P = kf->P + kf->Q;

    // Measurement Update
    kf->K = kf->P / (kf->P + kf->R);
    kf->x = kf->x + kf->K * (measurement - kf->x);
    kf->P = (1.0f - kf->K) * kf->P;

    return kf->x;
}
