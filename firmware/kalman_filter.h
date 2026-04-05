#ifndef KALMAN_FILTER_H
#define KALMAN_FILTER_H

/**
 * kalman_filter.h - 1D Kalman Filter Implementation
 * 
 * Niroop's Capstone Project
 * 
 * LEARNING JOURNEY:
 * Week 3: Tried simple moving average - still noisy
 * Week 4: Learned about Kalman filter - mind blown!
 * Week 4-5: Implemented basic version, tuned parameters
 * 
 * Tuning log:
 * Attempt 1: Q=0.1, R=1.0   → Smooth but slow to respond ✗
 * Attempt 2: Q=0.01, R=0.1  → Responsive but noisy ✗
 * Attempt 3: Q=0.01, R=0.5  → Goldilocks! ✓ (current)
 *
 * Resource: https://en.wikipedia.org/wiki/Kalman_filter
 *           Professor's recommended textbook Chapter 8
 */

#include "config.h"
#include <cmath>

/**
 * @class KalmanFilter1D
 * @brief Simple 1D Kalman filter for smoothing measurements
 * 
 * Algorithm:
 * 1. Prediction: Predict what state will be (based on model)
 *    P = P + Q  (uncertainty grows)
 * 
 * 2. Measurement: Get sensor reading
 * 
 * 3. Calculate Kalman gain: How much to trust measurement vs model
 *    K = P / (P + R)  (ranges 0 to 1)
 * 
 * 4. Update: Blend model prediction with measurement
 *    x = x + K * (z - x)  (z = measurement)
 * 
 * 5. Update uncertainty
 *    P = (1 - K) * P
 * 
 * Key insight: When K≈1, trust sensor. When K≈0, trust model.
 */
class KalmanFilter1D {
private:
    float x;              // State estimate (filtered value)
    float P;              // Estimate error covariance (uncertainty)
    float Q;              // Process noise (how much we trust our model)
    float R;              // Measurement noise (how much sensor noise)
    bool initialized;     // To handle first reading
    
    // DEBUG: Keep track of updates for analysis
    // int update_count = 0;  // Could log this later
    
public:
    /**
     * Constructor - set noise parameters
     * 
     * @param process_noise Q - Lower = trust model, Higher = responsive
     * @param measurement_noise R - Lower = trust sensor, Higher = damped
     * 
     * Tuning advice from Professor:
     * - Start with Q=0.01, R=0.5 and adjust from there
     * - If output lags real changes: increase Q
     * - If output too jumpy: increase R
     */
    KalmanFilter1D(float process_noise = KALMAN_Q,
                   float measurement_noise = KALMAN_R)
        : x(0.0f), 
          P(1.0f),              // Start uncertain about state
          Q(process_noise), 
          R(measurement_noise), 
          initialized(false) {
        // Note: P=1.0 is arbitrary starting covariance
        // Converges quickly regardless of initial value
    }
    
    /**
     * Update filter with new measurement
     * @param measurement Raw sensor reading
     * @return Filtered estimate (noise reduced)
     * 
     * This function does the full prediction-update cycle.
     * Should be called once per sensor read.
     */
    float update(float measurement) {
        if (!initialized) {
            // First call: just copy the measurement as our initial estimate
            // No filtering yet (need more data)
            x = measurement;
            initialized = true;
            return x;
        }
        
        // ===== PREDICTION STEP =====
        // Over time, we lose confidence in our model
        // (things could change!)
        P = P + Q;
        
        // ===== KALMAN GAIN CALCULATION =====
        // How much should we trust the new measurement?
        // High P (uncertain about model) → K ≈ 1 (trust sensor)
        // High R (noisy sensor) → K ≈ 0 (trust model)
        float K = P / (P + R);
        
        // ===== UPDATE STATE =====
        // New estimate = old estimate + Kalman gain × innovation
        // Innovation = (measurement - estimate) = how surprised we are
        float innovation = measurement - x;
        x = x + K * innovation;
        
        // ===== UPDATE COVARIANCE =====
        // Measurement reduced our uncertainty
        P = (1.0f - K) * P;
        
        return x;
    }
    
    /**
     * Get current estimate without updating
     * Useful for reading state in multiple places
     */
    float getEstimate() const {
        return x;
    }
    
    /**
     * Reset filter - useful if sensors restart
     */
    void reset() {
        x = 0.0f;
        P = 1.0f;
        initialized = false;
    }
};

#endif // KALMAN_FILTER_H
