# Project Map (Beginner-First)

Use this page to quickly locate responsibility boundaries across the repository.

## 1) Entry Points

- `README.md`: Primary project documentation and run commands.
- `run_dashboard.bat`: Preferred Windows launcher (simulator + dashboard).
- `run_wokwi_bridge.bat`: Preferred Wokwi bridge launcher.

## 2) Runtime Application (Python)

- `src/dashboard.py`: Dashboard entry point and runtime orchestration.
- `src/config.py`: Centralized constants, thresholds, and shared paths.
- `src/serial_reader.py`: Serial ingestion from hardware/bridge.
- `src/serial_simulator.py`: Local telemetry simulator.
- `src/alerts.py`: Alert generation and delivery logic.
- `src/analytics.py`: Runtime analytics and trend logic.
- `src/telemetry_schema.py` and `src/validators.py`: Contract/schema enforcement.

## 3) Firmware Runtime

- `firmware/main.ino`: Firmware entry point.
- `firmware/config/serial_protocol.h`: Canonical firmware packet contract.
- `firmware/config/config.h`: TTC threshold definitions (must match Python).
- `firmware/alerts/`: On-device alert behavior.
- `firmware/sensors/`: Sensor interfaces and adapters.

## 4) Bridge & Integration

- `bridge/wokwi_serial_bridge.py`: Wokwi stream normalization and forwarding.

## 5) Validation & Quality

- `validation/protocol_contract_test.py`: 7-field protocol contract checks.
- `validation/evaluate_synthetic.py`: Synthetic scenario evaluation.
- `validation/compare_wokwi_baseline.py`: Baseline comparison workflow.
- `tests/`: Unit tests for Python modules.

## 6) Data, Logs, and Models

- `dataset/`: Source synthetic/reference datasets.
- `LOGS/`: Runtime/session outputs (ignored generated data).
- `MODELS/`: Optional ML artifacts (fallback behavior required if missing).
- `ml/`: Training and inference support code.

## 7) Documentation

- `docs/README.md`: Documentation index.
- `docs/serial_protocol.md`: Telemetry contract specification.
- `docs/wokwi_bridge_smoke_test.md`: Bridge workflow and checks.
- `docs/simulation-validation-checklist.md`: Simulation regression checklist.
- `docs/naming-and-structure-policy.md`: Mandatory naming and folder rules.

## 8) Hardware Documentation

- `hardware/README.md`: Hardware docs index.
- `hardware/wiring_guide.md`: Wiring and pin map reference.
- `hardware/assembly_checklist.md`: Build and bring-up checklist.

## 9) Dependency & Tooling Files

- `requirements.txt`: Runtime dependencies.
- `requirements-dev.txt`: Development/test dependencies.
- `.gitignore`: Generated output and local-environment exclusions.

## Placement Rules

- Runtime behavior changes belong in `src/`, `firmware/`, or `bridge/`.
- Validation workflows belong in `validation/` and `tests/`.
- User-facing guidance belongs in `docs/`.
- Hardware build guidance belongs in `hardware/`.

## Continuous Quality Tasks

- `Quality: Ensure Dev Dependencies`
- `Quality: Lint`
- `Quality: Unit Tests`
- `Quality: Protocol Contract`
- `Quality: Synthetic Validation`
- `Wokwi: Smoke Test`
- `Quality: Full Gate`

## Sync Rules

- Keep telemetry format synchronized across `firmware/`, `bridge/`, `src/`, and `validation/`.
- Keep threshold values synchronized between `src/config.py` and `firmware/config/config.h`.
- Keep documentation links synchronized whenever files are moved or renamed.
