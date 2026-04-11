# Project Map (Beginner-First)

Use this page when you want to quickly find where things belong.

## 1) Start Here

- `README.md`: Main project guide and setup steps
- `run_dashboard.bat`: Fastest way to launch on Windows

## 2) Core Runtime Code

- `src/`: Main Python app
- `src/dashboard.py`: Dashboard entry point
- `src/config.py`: Shared settings and thresholds
- `src/serial_reader.py`: Reads telemetry from serial ports
- `src/validators.py`: Validation helpers

## 3) Firmware Side

- `firmware/main.ino`: Firmware entry point
- `firmware/config/`: Firmware configuration and protocol headers
- `firmware/alerts/`: Alert output logic
- `firmware/sensors/`: Sensor interfaces

## 4) Bridge & Simulation

- `bridge/wokwi_serial_bridge.py`: Wokwi bridge and forwarding
- `src/serial_simulator.py`: Local simulator

## 5) Validation & Tests

- `validation/`: End-to-end validation scripts
- `tests/`: Unit tests

## 6) Data & Models

- `LOGS/`: Recorded runtime sessions
- `dataset/`: Synthetic/reference datasets
- `MODELS/`: Optional trained model artifacts
- `ml/`: ML-related training/inference code

## 7) Docs

- `docs/serial_protocol.md`: Telemetry contract details
- `docs/wokwi_bridge_smoke_test.md`: Bridge smoke test guide
- `docs/QUICK_START.txt`: Quick commands and troubleshooting
- `docs/archive/housekeeping/`: Historical cleanup notes

## 8) Configuration

- `requirements.txt`: Runtime Python dependencies
- `requirements-dev.txt`: Dev/test dependencies

## Rule of Thumb

- If code affects runtime behavior, keep it in `src/`, `firmware/`, or `bridge/`.
- If it explains usage, keep it in `docs/`.
- If it is one-time cleanup history, keep it under `docs/archive/housekeeping/`.
