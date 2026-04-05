#pragma once

class KalmanFilter1D {
private:
    float x; // State: estimated distance
    float p; // Covariance
    float q; // Process noise
    float r; // Measurement noise
    bool initialized;

public:
    KalmanFilter1D(float processNoise = 0.01f, float measurementNoise = 0.5f, float initialError = 1.0f) {
        q = processNoise;
        r = measurementNoise;
        p = initialError;
        x = 0.0f;
        initialized = false;
    }

    float update(float measurement) {
        if (!initialized) {
            x = measurement;
            initialized = true;
            return x;
        }

        // Prediction update
        p = p + q;

        // Measurement update
        float k = p / (p + r);
        x = x + k * (measurement - x);
        p = (1 - k) * p;

        return x;
    }

    float getState() const { return x; }
    void reset() { initialized = false; }
};
