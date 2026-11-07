# Synthetic Kinematic Dataset

This directory contains reference kinematic datasets used for testing, validation, and ML training of the TTC Collision Risk System.

## File Information
- **File:** `synthetic_ttc_validation.csv`
- **Total Samples:** 610 timesteps (at 100ms intervals)
- **Scenarios Included:**
  1. `safe_cruise` (100 samples): Cruising at a safe trailing distance ($>40\,\text{m}$), TTC $>3.0\,\text{s}$ (SAFE).
  2. `slow_closing` (100 samples): Gradual closure in dense traffic from $22\,\text{m} \to 1.2\,\text{m}$, crossing into WARNING.
  3. `sudden_braking` (110 samples): Hard emergency deceleration ahead, triggering rapid transition to CRITICAL.
  4. `fast_collision` (90 samples): High-speed rapid approach reaching physical collision headway.
  5. `noisy_sensor` (100 samples): Realistic Gaussian measurement noise injected into ultrasonic distance readings.
  6. `wet_road_threshold_shift` (110 samples): Evaluates dynamic safety threshold expansion under reduced tyre-road friction ($1.4\times$ multiplier).

## Telemetry Fields (Canonical 7-Field Format)
```text
timestamp_ms, distance_cm, speed_kmh, ttc_basic, ttc_ext, risk_class, confidence
```
| Field | Unit | Description |
|---|---|---|
| `timestamp_ms` | milliseconds | Monotonic time since scenario start |
| `distance_cm` | centimeters | Relative gap between host bumper and lead obstacle |
| `speed_kmh` | km/h | Host vehicle speed |
| `ttc_basic` | seconds | Constant-velocity Time-to-Collision ($d / v_{\text{close}}$) |
| `ttc_ext` | seconds | Constant-deceleration Time-to-Collision ($5.0\,\text{m/s}^2$ braking limit) |
| `risk_class` | integer | Ground-truth risk state: `0=SAFE`, `1=WARNING`, `2=CRITICAL` |
| `confidence` | float | Signal confidence score between $0.00$ and $1.00$ |

## Generation
To regenerate this dataset, run:
```bash
python src/synthetic_validation_dataset.py
```
