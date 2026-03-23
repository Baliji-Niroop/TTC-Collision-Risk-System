# Understanding the Project

The central idea behind this project is one question:

**How much time is left before a collision, if the vehicle keeps approaching at its current speed?**

That number is called Time-to-Collision (TTC).

## How TTC works

The system takes two inputs:
1. Distance to the obstacle ahead
2. Closing speed toward that obstacle

From those, it calculates TTC and classifies the situation:

- **SAFE** — more than 3.0 seconds remaining
- **WARNING** — between 1.5 and 3.0 seconds
- **CRITICAL** — 1.5 seconds or less

Lower TTC means less time to react.

## System pipeline

1. Telemetry comes in (from simulator, log file, or ESP32 serial)
2. Values are validated for sanity
3. Risk is classified using ML or physics fallback
4. Dashboard updates: live metrics, charts, event log, session stats

## Input modes

### Simulator
Generates synthetic approach data directly inside the dashboard process. No hardware needed. Good for demos and testing.

### Live Log
Dashboard reads the latest line from `LOGS/live_data.txt`. That file gets updated by either `serial_simulator.py` or `serial_reader.py`.

### ESP32 Serial
Reads directly from USB serial using `pyserial`. Requires an ESP32 sending data in the expected 7-field format.

## Key components

**`dashboard.py`** — The main interface. Collects telemetry, loads the ML model (or falls back to TTC thresholds), and displays everything.

**`serial_simulator.py`** — Creates fake telemetry for testing. Simulates a vehicle approaching, computes TTC, writes to `LOGS/live_data.txt`.

**`serial_reader.py`** — Reads real serial data from an ESP32 and logs it. Saves full sessions as CSV on exit.

**`validators.py`** — Checks that incoming data is valid and physically plausible. Rejects bad rows, flags anomalies.

**`alerts.py`** — Fires alerts on critical/warning events with throttling to avoid spam.

**`analytics.py`** — Tracks session-level statistics: trend direction, TTC stats, collision probability estimates.

**`safety_features.py`** — Extra protection: hysteresis to reduce flickering, sensor fault detection, velocity sanity checks, ML-physics confidence fusion.

## TTC calculation

Two variants are calculated:
- **Basic TTC**: assumes closing speed stays constant → `distance / speed`
- **Extended TTC**: assumes the vehicle decelerates → solved from kinematics

Both are shown on the dashboard so you can see both the worst-case and the more realistic estimate.

## ML vs physics

- If the trained model file exists and loads, the dashboard uses it for prediction.
- If the model is missing or incompatible, the system falls back to simple TTC threshold rules.

This fallback is important — it means the dashboard always works, even without the ML model.

## What's still missing

The software is in good shape. What's not done yet:
- ESP32 firmware
- Physical sensor hardware
- Calibration and field testing

So right now, this is a working software prototype waiting for the hardware side.

## Configuration

All settings live in `PYTHON/config.py`:
- TTC thresholds
- Serial baud rate and timeout
- Simulator parameters
- Dashboard refresh rate
- Logging options

## Further reading

- `README.md` — setup and run instructions
- `status.md` — project progress and what's left
- `SERIAL_PROTOCOL.md` — the exact packet format for ESP32 firmware
- `INTEGRATION_STATUS.md` — hardware integration checklist
