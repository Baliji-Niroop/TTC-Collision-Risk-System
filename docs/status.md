# TTC Collision Risk System — Project Status

Last updated: March 24, 2026
Current state: software prototype, hardware integration pending
Estimated completion: 55–60%

## Where things stand

The Python side of the project is built and working in simulation mode. The Streamlit dashboard shows live TTC monitoring and the ML model loads and predicts correctly. The serial reader is ready to receive ESP32 data whenever hardware is available.

The main gap is on the hardware side — no ESP32 firmware has been written yet, no sensor has been wired, and no real-world testing has happened.

**Working now:**

- Simulator pipeline.
- Dashboard (live metrics, charts, event log, session stats).
- ML model loading with physics fallback.
- Serial reader (Python side).
- Logging, validation, analytics modules.

**Not done yet:**

- Hardware procurement and wiring.
- ESP32 firmware.
- Sensor calibration.
- Real-world TTC validation.
- Latency and false-alarm testing.

## Completion by area

| Area | Progress |
|------|----------|
| Software architecture | 90% |
| Dashboard and simulator | 90% |
| Python serial interface | 85% |
| ML integration | 80% |
| Hardware setup | 0% |
| ESP32 firmware | 0% |
| Real-world validation | 0% |
| **Overall** | **55–60%** |

## Software checklist

### Done

- [x] Modular project structure.
- [x] Streamlit dashboard with three input modes.
- [x] Physics-based simulator.
- [x] ML model with TTC threshold fallback.
- [x] Centralized config (`src/config.py`).
- [x] Telemetry validation and anomaly detection.
- [x] Alert throttling and dispatch.
- [x] Session analytics module.
- [x] Safety features (hysteresis, fault detection, velocity sanity, fusion).
- [x] Rotating file logger.
- [x] Serial reader for ESP32.
- [x] One-click Windows launcher (`run_dashboard.bat`).

### Blocked by hardware

- [ ] ESP32 firmware emitting 7-field packets.
- [ ] Sensor wiring and board bring-up.
- [ ] Real distance measurement validation.
- [ ] Speed acquisition strategy finalized.
- [ ] End-to-end ESP32-to-dashboard test.

### Future work

- [ ] Real-world TTC validation runs.
- [ ] False-positive/negative analysis.
- [ ] Alert latency measurements.
- [ ] Confusion matrix on real telemetry.
- [ ] Final report and presentation.

## Blockers

- No hardware has been procured or connected yet.
- ESP32 firmware does not exist yet.
- The serial protocol has not been tested on actual hardware.
- No physical sensor calibration data exists.

## Note on serial_reader.py

This is a real, working Python component — not a placeholder. It will read and log serial data as soon as an ESP32 starts sending packets in the expected format. The missing piece is entirely on the microcontroller side.

## Validation readiness

| Item | Ready? | Notes |
|------|--------|-------|
| Simulator demo | Yes | Can show now |
| Dashboard demo | Yes | Can show now |
| ML inference demo | Yes | Model loads, fallback works |
| Sensor accuracy test | No | Needs hardware |
| TTC accuracy test | No | Needs physical measurements |
| Serial integration test | Partial | Python side ready, ESP32 missing |
| Alert latency test | No | Needs end-to-end test |
| Confusion matrix | No | Needs field data |

## Module summary

| Module | What it does |
|--------|-------------|
| `dashboard.py` | Main monitoring UI (Simulator, Live Log, ESP32 Serial) |
| `serial_simulator.py` | Writes synthetic telemetry to `LOGS/live_data.txt` |
| `serial_reader.py` | Reads ESP32 serial data, logs sessions to CSV |
| `config.py` | All settings in one place |
| `validators.py` | Parses, validates, and anomaly-checks telemetry |
| `alerts.py` | Throttled alert dispatch |
| `analytics.py` | Session stats, TTC trends, collision probability |
| `safety_features.py` | Hysteresis, fault detection, velocity sanity, fusion |
| `logger.py` | Rotating file and console logging |
| `utils.py` | Health checks, environment validation |

## What to do next

1. Lock the telemetry format (see `docs/serial_protocol.md`).
2. Get the ESP32 and sensor hardware.
3. Write minimal firmware that outputs valid 7-field packets.
4. Run first serial test with `serial_reader.py`.
5. Validate distance accuracy and TTC with physical measurements.
