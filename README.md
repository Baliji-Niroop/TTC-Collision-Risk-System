# TTC - Time-To-Collision Risk Prediction System

Professional, modular collision-risk pipeline for firmware + Python analytics.

## Overview

This repository provides:

- Real-time telemetry ingestion from hardware, simulator, or Wokwi bridge.
- TTC and risk classification with fixed protocol guarantees.
- Live dashboard with alerts.
- Validation tooling for protocol and synthetic scenarios.

Core telemetry contract (frozen, 7 fields):

```text
timestamp_ms, distance_cm, speed_kmh, ttc_basic, ttc_ext, risk_class, confidence
```

Risk thresholds (must stay synchronized across firmware and Python):

- critical: 1.5s
- warning: 3.0s

## How It Works

The runtime emits alerts only after these safety checks are evaluated:

1. Telemetry packet is valid against the 7-field contract.
2. Distance and speed values are within acceptable ranges.
3. TTC is computed using basic and extended logic.
4. Final risk class is selected using thresholds (or ML if available).

If data is invalid or incomplete, the pipeline defaults to safe handling (reject packet / avoid unsafe escalation).

## Quick Start

### 1) Environment setup

Windows:

```bat
python -m venv ttc_env
ttc_env\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Linux/macOS:

```bash
python -m venv ttc_env
source ttc_env/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 2) Start the dashboard stack

```bat
run_dashboard.bat
```

### 3) Optional: start Wokwi bridge

```bat
run_wokwi_bridge.bat
```

## Validation Commands

```bat
ttc_env\Scripts\python.exe validation\protocol_contract_test.py
ttc_env\Scripts\python.exe validation\evaluate_synthetic.py
ttc_env\Scripts\python.exe validation\compare_wokwi_baseline.py --input LOGS\session_YYYYMMDD_HHMMSS.csv
```

Bridge smoke test:

```bat
echo 1000,120,30,2.40,2.20,2,0.85 | ttc_env\Scripts\python.exe bridge\wokwi_serial_bridge.py --source stdin --no-launch-stack
```

## Very Important Before Hardware Flashing

- Flash only the root Arduino entry sketch: `TTC.ino`.
- Keep active firmware logic in `firmware/main.ino` and firmware headers under `firmware/`.
- Do not treat bridge/simulation scripts as firmware targets.
- Pin mapping source of truth is `firmware/pinmap.h`.

## Main Tuning Values

Primary tuning constants live in `firmware/config/config.h`:

- `TTC_CRITICAL_S`
- `TTC_WARNING_S`
- `PACKET_INTERVAL_MS`
- `DEFAULT_DECEL_MS2`
- `FUSION_US_WEIGHT`
- `FUSION_LIDAR_WEIGHT`

Mirror threshold values in `src/config.py` to avoid risk-class drift.

## Validation Checklist

Use `docs/simulation-validation-checklist.md` after any significant change to firmware, bridge, or TTC logic.

## Repository Layout

```text
TTC/
  firmware/     # Embedded runtime, protocol headers, alert logic
  hardware/     # Wiring and assembly guides
  src/          # Python runtime: ingest, analytics, alerts, dashboard
  bridge/       # Wokwi/serial bridging tools
  validation/   # Contract checks and synthetic evaluation
  tests/        # Unit tests
  docs/         # Architecture, protocol, setup and workflow docs
  LOGS/         # Runtime logs/session artifacts (ignored by git)
  MODELS/       # Optional ML artifacts (fallback-safe)
  dataset/      # Synthetic/reference datasets
```

## 7-Part Roadmap

1. Runtime logic: `src/`
2. Embedded firmware: `firmware/`
3. Serial and Wokwi bridge: `bridge/`
4. Validation and test gates: `validation/` and `tests/`
5. Data and generated outputs: `dataset/`, `LOGS/`, `MODELS/`
6. Documentation and hardware guides: `docs/` and `hardware/`
7. Project tooling and launchers: `requirements.txt`, `requirements-dev.txt`, `run_*.bat`, `wokwi.toml`, `.gitignore`

## Architecture Flow

```text
Sensor/Simulator -> Ingestion -> Validation -> TTC/Risk -> Alerts/UI -> Logs
```

Primary code ownership:

- Firmware runtime: `firmware/main.ino` and `firmware/config/serial_protocol.h`
- Ingestion/normalization: `src/serial_reader.py`, `src/serial_simulator.py`, `bridge/wokwi_serial_bridge.py`
- UI and analytics: `src/dashboard.py`, `src/alerts.py`, `src/analytics.py`
- Replay/validation: `src/replay_runner.py`, `validation/`

## Documentation

- `docs/README.md` - Documentation index
- `docs/PROJECT_MAP.md` - Beginner-first map of modules
- `docs/serial_protocol.md` - Telemetry protocol contract
- `docs/wokwi_bridge_smoke_test.md` - Wokwi validation workflow
- `docs/simulation-validation-checklist.md` - Simulation regression checklist
- `docs/naming-and-structure-policy.md` - Naming, folder, and contribution policy
- `hardware/README.md` - Hardware docs index and links

## Continuous Quality Gate

Run these VS Code tasks before sharing or merging changes:

- `Quality: Ensure Dev Dependencies`
- `Quality: Lint`
- `Quality: Unit Tests`
- `Quality: Protocol Contract`
- `Quality: Synthetic Validation`
- `Wokwi: Smoke Test`
- `Quality: Full Gate`

## Professional Conventions

- Keep constants/thresholds centralized in `src/config.py`.
- Keep protocol aligned with `firmware/config/serial_protocol.h`.
- Reuse `src/telemetry_schema.py` and `src/validators.py` for parsing/validation.
- Do not hardcode TTC thresholds in feature modules.
- Optional ML must degrade gracefully when `MODELS/ml_model.pkl` is unavailable.

## Troubleshooting

- Protocol errors: run `validation/protocol_contract_test.py`.
- Missing model: fallback to TTC threshold logic is expected behavior.
- Wokwi COM pairing: bridge write/read ports must be paired but different.

## Notes

- Firmware packet format must stay aligned with `firmware/config/serial_protocol.h`.
- Keep TTC thresholds synchronized between `src/config.py` and `firmware/config/config.h`.

## Contributing

Keep changes focused and route them to the correct layer:

- Runtime behavior: `src/`
- Firmware behavior: `firmware/`
- Bridge logic: `bridge/`
- Validation and tests: `validation/` and `tests/`
- Documentation: `docs/` and `hardware/`

Before opening a pull request, run the quality tasks in `.vscode/tasks.json` or the equivalent scripts in `validation/`.
