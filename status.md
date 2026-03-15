# TTC Collision Risk Monitoring System - Status Tracker

Last synced: March 15, 2026
Project state: software prototype with hardware integration pending
Overall completion estimate: 55-60%

## Executive Summary

The Python system is substantially built and usable today in simulation.

- The Streamlit dashboard runs.
- The simulator runs.
- The trained ML model file exists in `MODELS/ml_model.pkl`.
- The Python serial reader is implemented and ready to receive ESP32 telemetry.
- Logging, validation, analytics, and safety-support modules are present.

The main blocker is not software structure. The main blocker is that real hardware and firmware validation have not happened yet.

## Current Reality Snapshot

```text
Working now:
- Simulator pipeline
- Dashboard visual monitoring
- ML model loading and fallback TTC logic
- Python-side serial ingestion path
- Logging, analytics, and validation helpers

Not complete yet:
- Hardware procurement and wiring
- ESP32 firmware implementation
- Real sensor calibration
- Real TTC accuracy validation
- Latency and false-alarm testing
```

## Completion Breakdown

This estimate is meant to reflect the real state of the project rather than only checklist count.

| Area | Status |
| ---- | ------ |
| Software architecture | 90% |
| Dashboard and simulator | 90% |
| Python serial interface | 85% |
| ML integration | 80% |
| Hardware setup | 0% |
| ESP32 firmware | 0% |
| Real-world validation | 0% |
| Overall project | 55-60% |

## Software Checklist

### Completed

- [x] Modular project structure in place
- [x] Streamlit dashboard implemented
- [x] Physics-based simulator implemented
- [x] ML model integrated with fallback TTC logic
- [x] Centralized configuration in `config.py`
- [x] Telemetry validation and anomaly checks implemented
- [x] Alert handling implemented
- [x] Session analytics implemented
- [x] Safety-support logic implemented in `safety_features.py`
- [x] Logging pipeline implemented
- [x] Python serial reader implemented
- [x] One-click Windows launcher implemented

### In progress or blocked by hardware

- [ ] ESP32 firmware emitting the agreed 7-field packet format
- [ ] Sensor wiring and board bring-up
- [ ] Real distance measurement validation
- [ ] Vehicle speed acquisition strategy finalized
- [ ] End-to-end ESP32 to dashboard testing

### Future validation and delivery

- [ ] Real-world TTC validation runs
- [ ] False-positive and false-negative analysis
- [ ] Alert latency measurements
- [ ] Confusion matrix using real telemetry
- [ ] Final academic report and presentation package

## Main Blockers

- Hardware components are not yet procured or connected.
- ESP32 firmware is not yet implemented.
- Real telemetry protocol has not been validated on actual hardware.
- No physical sensor calibration or field-test data exists yet.

## Important Clarification

`serial_reader.py` is already a real, usable Python-side integration component. The missing part is the microcontroller side that must send data in the expected format.

That means the serial communication path should be treated as:

- Python receiver: mostly ready
- ESP32 sender: not started
- end-to-end hardware validation: not started

## Validation Readiness

| Validation item | Ready? | Notes |
| ---- | ---- | ---- |
| Simulator demo | Yes | Can be shown now |
| Dashboard demo | Yes | Can be shown now |
| ML inference demo | Yes | Uses existing model and fallback logic |
| Sensor accuracy test | No | Needs hardware |
| TTC accuracy test | No | Needs physical measurements |
| Serial integration test | Partial | Python side ready, ESP32 side missing |
| Alert latency test | No | Needs end-to-end runtime test |
| Confusion matrix on real data | No | Needs recorded field data |

## Synchronized Module Summary

- `dashboard.py`: main monitoring interface with Simulator, Live Log, and ESP32 Serial modes
- `serial_simulator.py`: synthetic telemetry generator writing to `LOGS/live_data.txt`
- `serial_reader.py`: serial ingestion and session logging for real hardware
- `config.py`: shared thresholds, serial config, simulator config, logging config
- `validators.py`: telemetry parsing, validation, anomaly checks, safety-feature bootstrap
- `alerts.py`: alert throttling and dispatch
- `analytics.py`: session summaries, TTC statistics, trend estimates
- `safety_features.py`: hysteresis, sensor fault detection, sanity filtering, ML-confidence fusion
- `logger.py`: rotating file and console logging
- `utils.py`: environment and system helper routines

## Near-Term Priority Order

1. Freeze the telemetry format in `SERIAL_PROTOCOL.md`.
2. Procure and wire the ESP32 and sensor hardware.
3. Implement ESP32 firmware to match the documented packet format.
4. Run first end-to-end serial test into `serial_reader.py`.
5. Validate distance accuracy and TTC behavior with real measurements.

## Recent Synchronization Update

March 15, 2026:

- README was rewritten to match actual code behavior.
- Project docs were synchronized to reflect that the software side is ahead of the hardware side.
- Serial protocol expectations were documented explicitly.
- Hardware integration work was separated into its own checklist so the remaining work is clearer.
