# TTC Collision Risk Prediction

Industry-grade, runtime-safe TTC collision risk project with firmware telemetry, Python ingestion, validation workflows, and a Streamlit dashboard.

## Project Overview

This repository predicts and visualizes collision risk from Time-to-Collision values using a strict telemetry contract and a hybrid inference strategy:

- Primary logic: TTC threshold classification
- Optional logic: ML model inference
- Guaranteed fallback: TTC threshold classification when model is missing/unavailable

Current baseline is software-stable and Wokwi-validated.

## Architecture

- firmware/: embedded packet emission and local risk fallback logic
- python/: normalized Python architecture modules
- dashboard/: dashboard application structure and UI boundaries
- ml/: inference/training/model/dataset structure
- bridge/: Wokwi serial bridge runtime
- docs/: source-of-truth documentation
- assets/: diagrams, screenshots, demos
- tests/: test entrypoints and references
- scripts/: launcher wrappers and helper scripts

Runtime compatibility guarantee:

- Existing launchers and source entrypoints remain valid.
- src/ remains the active compatibility layer while normalized folders are adopted.

## Quick Start

One-click launcher:

```cmd
run_dashboard.bat
```

Wokwi bridge stack:

```cmd
run_wokwi_bridge.bat
```

Manual dashboard run:

```cmd
python src\serial_simulator.py
python -m streamlit run src\dashboard.py --server.headless true
```

Normalized dashboard entrypoint is also available:

```cmd
python -m streamlit run dashboard\app.py --server.headless true
```

## Canonical Telemetry Contract

```text
timestamp_ms,distance_cm,speed_kmh,ttc_basic,ttc_ext,risk_class,confidence
```

Risk thresholds:

- critical: TTC <= 1.5s
- warning: 1.5s < TTC <= 3.0s
- safe: TTC > 3.0s

## Validation

```cmd
python validation\protocol_contract_test.py
python validation\evaluate_synthetic.py
python validation\compare_wokwi_baseline.py --input LOGS\session_YYYYMMDD_HHMMSS.csv
```

## Folder Map

- firmware/
	- config/, sensors/, alerts/, ml/
- python/
	- analytics/, utils/, serial/, simulation/
- dashboard/
	- app.py, components/, pages/
- ml/
	- inference/, training/, models/, datasets/
- bridge/
- docs/
	- executive_summary.md
	- full_study.md
	- workflow_guide.md
	- migration_blueprint.md

## Source-of-Truth Docs

- docs/executive_summary.md
- docs/full_study.md
- docs/workflow_guide.md
- docs/migration_blueprint.md

Legacy master-doc names remain as pointer files for compatibility.

## Current Implementation Status

- Dashboard modes are operational (simulator, live log, ESP32 serial)
- Wokwi bridge pipeline is operational
- Protocol contract checks pass
- Synthetic evaluation pipeline is operational
- Physical sensor deployment remains pending hardware procurement

## Roadmap

1. Complete remaining runtime-safe module migration from src/ into normalized package folders.
2. Add CI test orchestration under tests/.
3. Integrate hardware telemetry validation and field scenario testing.

## Setup

```cmd
python -m venv ttc_env
ttc_env\Scripts\activate.bat
pip install -r requirements.txt
```
