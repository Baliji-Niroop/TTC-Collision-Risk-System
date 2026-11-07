# How TTC and Risk Classification Work

This page describes the implemented kinematic calculations and configured risk thresholds. These calculations are a prototype, not a safety-certified ADAS.

## Inputs

- `distance_cm`: measured distance to an object.
- `speed_kmh`: host-vehicle speed.
- Closing speed: estimated by firmware from changes in distance over time.
- Deceleration: firmware uses the configured default unless the optional IMU update is enabled.

The project does not independently measure the lead vehicle's speed.

## Basic TTC

For positive closing speed, the constant-speed estimate is:

\[
\mathrm{TTC}_{basic} = \frac{d}{v_{closing}}
\]

Here, distance is in meters and closing speed is in meters per second. A non-positive or very low closing speed is treated as no immediate collision; the implementation uses a capped value rather than infinity.

## Extended TTC

The deceleration model solves for the earliest time when the estimated gap reaches zero:

\[
d(t) = d - v_{closing}t + \frac{1}{2}at^2
\]

The discriminant is:

\[
\Delta = v_{closing}^2 - 2ad
\]

If the discriminant is negative, the implementation returns its no-collision cap (99 seconds). Otherwise it uses the earlier root:

\[
\mathrm{TTC}_{ext} = \frac{v_{closing} - \sqrt{v_{closing}^2 - 2ad}}{a}
\]

The configured default deceleration is 5.0 m/s². It is a project setting, not a measured braking capability.

## Risk classes

The base thresholds in [`src/config.py`](../src/config.py) and [`firmware/config/config.h`](../firmware/config/config.h) are:

| Class | Label | TTC |
|---:|---|---|
| 0 | SAFE | greater than 3.0 s |
| 1 | WARNING | greater than 1.5 s and at most 3.0 s |
| 2 | CRITICAL | at most 1.5 s |

The optional `RiskHysteresisFilter` has a 0.3 s deadband when leaving higher-risk states. It is initialized by validation code but is not applied by the live dashboard. See the [risk-state diagram](architecture.md#2-risk-states-and-hysteresis).

The firmware's current main loop sets `roadCondition` to dry (`0`). The TTC helper code contains surface multipliers, but the firmware main loop does not currently select a wet, gravel, or ice condition.

## Synthetic labels and model limits

The generated dataset labels each row from TTC thresholds (including the wet-scenario thresholds). A model evaluated against these labels is being compared with the rule that created them. Even a high score does not establish accuracy on real roads or with real sensor noise. The held-out split and its metrics are described in [results](../results/README.md).

## Implementation references

- Python TTC helper: `src/ttc_engine.py`
- Firmware TTC helper: `firmware/ml/ttc_engine.h`
- Firmware classification and optional override: `firmware/alerts/risk_classifier.h`
- Dataset label generation: `src/synthetic_validation_dataset.py`
- Telemetry field definitions: [serial protocol](serial_protocol.md)
