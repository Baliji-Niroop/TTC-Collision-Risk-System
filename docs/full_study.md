# Full Study Document

## 1. Problem Definition
The system predicts collision risk from Time-to-Collision (TTC), computed from distance and closing speed. It must classify risk consistently, expose live operational telemetry, and remain functional even when machine-learning inference is unavailable.

## 2. Canonical System Definition

### 2.1 Telemetry contract (frozen)
```
timestamp_ms,distance_cm,speed_kmh,ttc_basic,ttc_ext,risk_class,confidence
```

### 2.2 Risk classes
- SAFE: TTC > 3.0s
- WARNING: 1.5s < TTC <= 3.0s
- CRITICAL: TTC <= 1.5s

### 2.3 Source of threshold truth
- Python: `src/config.py`
- Firmware: `firmware/config.h`

Both must remain synchronized.

## 3. Current Architecture

### 3.1 Embedded layer
- `firmware/main.ino` orchestrates packet emission.
- `firmware/ttc_engine.h` computes TTC values.
- `firmware/risk_classifier.h` classifies risk.
- `firmware/serial_protocol.h` emits canonical packets.

Current limitation: `firmware/sensors.h` uses simulated distance and fixed speed/confidence values.

### 3.2 Python runtime layer
- `src/dashboard.py`: monitoring UI and runtime orchestration.
- `src/serial_reader.py`: serial ingestion and session logging.
- `src/serial_simulator.py`: synthetic stream generation.
- `src/ml_inference.py`: model loading/prediction + fallback behavior.
- `src/validators.py` + `src/telemetry_schema.py`: packet validation/parsing.
- `src/alerts.py` + `src/analytics.py` + `src/safety_features.py`: runtime logic.

### 3.3 Validation layer
- `validation/protocol_contract_test.py`
- `validation/evaluate_synthetic.py`
- `validation/compare_wokwi_baseline.py`

### 3.4 Simulation/bridge layer
- Wokwi stack and bridge utilities under `bridge/` and `diagram.json`.

## 4. Real Execution Pipeline
1. Telemetry source produces canonical packet (simulator, bridge/log, or serial).
2. Packet is validated and parsed.
3. Risk is inferred via model if available, else TTC threshold fallback.
4. Alerts/analytics update runtime state.
5. Dashboard renders metrics/charts/event history.
6. Session artifacts are saved for replay and analysis.

## 5. Old vs Current Reality

| Topic | Legacy/Overstated Claim | Current Code Reality |
|---|---|---|
| Sensor fusion | Weighted multi-sensor fusion is active | Implemented in `sensors.h` (0.4×US + 0.6×LiDAR) |
| Kalman filtering | Implemented for noise suppression | Active 1D Kalman Filter running on distance reads |
| Speed source | Real encoder-based speed integrated | Speed derived from 3-read circular buffer (200ms) |
| Deceleration source | Real IMU deceleration integrated | MPU6050 Acceleration X-axis mapped to TTC Ext |
| Hardware validation | Physical stack validated end-to-end | Wokwi validated; physical validation pending |

## 6. Gaps and Risks
- Firmware sensor functions are placeholder implementations.
- Physical calibration and field metrics are unverified.
- Documentation can drift unless consolidated references are maintained.

## 7. Consolidated Improvement Plan

### Phase A - Firmware completion
- Implement real distance/speed/confidence sources.
- Preserve packet schema and threshold alignment.

### Phase B - Integration verification
- Validate serial ingestion from physical hardware.
- Confirm dashboard behavior in both serial and live-log modes.

### Phase C - Field validation
- Measure TTC accuracy, alert latency, and false-alarm behavior.
- Record repeatable evidence in `validation/outputs/`.

## 8. Final Status Statement
The project is a robust, simulation-validated TTC platform with strong software integration. The remaining critical work is physical sensor integration and field-grade validation.
