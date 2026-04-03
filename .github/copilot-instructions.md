# Project Guidelines

## Code Style
- Keep Python configuration, constants, and shared paths centralized in [src/config.py](src/config.py).
- Use the project logger in [src/logger.py](src/logger.py) for library/module code instead of ad-hoc prints.
- Reuse schema/validation helpers from [src/telemetry_schema.py](src/telemetry_schema.py) and [src/validators.py](src/validators.py) instead of custom CSV parsing.
- Keep firmware packet structure aligned with [firmware/serial_protocol.h](firmware/serial_protocol.h).

## Architecture
- Firmware emits canonical telemetry and local risk classification from [firmware/main.ino](firmware/main.ino) and headers in [firmware](firmware).
- Ingestion and normalization live in [src/serial_reader.py](src/serial_reader.py), [src/serial_simulator.py](src/serial_simulator.py), and [bridge/wokwi_serial_bridge.py](bridge/wokwi_serial_bridge.py).
- UI and runtime analytics live in [src/dashboard.py](src/dashboard.py), [src/alerts.py](src/alerts.py), and [src/analytics.py](src/analytics.py).
- Replay and validation workflows live in [src/replay_runner.py](src/replay_runner.py) and [validation](validation).
- Optional ML inference must degrade gracefully to TTC threshold logic in [src/ml_inference.py](src/ml_inference.py) and [src/dashboard.py](src/dashboard.py).

## Build and Test
- Preferred Windows launcher (simulator + dashboard):

    run_dashboard.bat

- Preferred Wokwi bridge launcher:

    run_wokwi_bridge.bat

- Environment setup:

    python -m venv ttc_env
    .\ttc_env\Scripts\activate.bat
    pip install -r requirements.txt

- Validation commands:

    .\ttc_env\Scripts\python.exe validation\protocol_contract_test.py
    .\ttc_env\Scripts\python.exe validation\evaluate_synthetic.py
    .\ttc_env\Scripts\python.exe validation\compare_wokwi_baseline.py --input LOGS\session_YYYYMMDD_HHMMSS.csv

## Conventions
- Treat telemetry as a frozen 7-field contract in this exact order: timestamp_ms, distance_cm, speed_kmh, ttc_basic, ttc_ext, risk_class, confidence.
- Keep TTC thresholds synchronized between [src/config.py](src/config.py) and [firmware/config.h](firmware/config.h): critical=1.5s, warning=3.0s.
- Do not introduce hardcoded thresholds in feature modules; read from shared config.
- Do not assume [MODELS/ml_model.pkl](MODELS/ml_model.pkl) exists; preserve fallback behavior.
- For Wokwi virtual COM usage, bridge write port and reader port must be paired but different ports.

## Docs
- Project orientation: [docs/understanding.md](docs/understanding.md)
- Telemetry contract: [docs/serial_protocol.md](docs/serial_protocol.md)
- Current status: [docs/status.md](docs/status.md)
- Hardware and integration checklist: [docs/integration_status.md](docs/integration_status.md)
- Wokwi validation workflow: [docs/wokwi_bridge_smoke_test.md](docs/wokwi_bridge_smoke_test.md)
- Virtual hardware details: [docs/wokwi_hardware_validation.md](docs/wokwi_hardware_validation.md)
- Roadmap and rationale: [docs/software_first_roadmap.md](docs/software_first_roadmap.md)
- Diagrams: [docs/diagrams/README.md](docs/diagrams/README.md)