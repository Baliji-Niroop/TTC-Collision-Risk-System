# Repository Audit and Cleanup Manifest

Date: 2026-04-04

## Phase 1 Audit Summary

### Duplicate or overlapping responsibilities found
- Legacy architecture docs duplicated with new master docs.
- Mixed python runtime responsibilities concentrated in src/ instead of domain folders.
- Firmware headers in a flat folder mixed config, sensor, and alert responsibilities.

### Outdated or clutter-prone assets found
- Legacy replay outputs under LOGS/replay_outputs (archived).
- __pycache__ directories across Python folders.
- Legacy uppercase master-doc naming no longer aligned with normalization standard.

### Entrypoints map
- Dashboard launcher: run_dashboard.bat
- Wokwi launcher: run_wokwi_bridge.bat
- Dashboard app runtime: src/dashboard.py (plus normalized wrapper dashboard/app.py)
- Serial reader: src/serial_reader.py
- Simulator: src/serial_simulator.py
- Replay: src/replay_runner.py
- Validation: validation/protocol_contract_test.py, validation/evaluate_synthetic.py, validation/compare_wokwi_baseline.py
- Bridge: bridge/wokwi_serial_bridge.py
- Firmware entrypoint: firmware/main.ino

### Dependency map (high-level)
- dashboard/app.py -> src/dashboard.py
- src/replay_runner.py -> src/alerts.py, src/analytics.py, src/ml_inference.py, src/telemetry_schema.py, src/validators.py
- src/analytics.py -> python/analytics package
- src/utils.py -> python/utils package
- src/ml_inference.py -> ml/inference package
- validation/evaluate_synthetic.py -> src/config.py and ml/inference package
- bridge/wokwi_serial_bridge.py -> src/validators.py, src/telemetry_schema.py, src/logger.py

## Phase 2 Structure Normalization

Implemented normalized target boundaries:
- firmware/{config,sensors,alerts,ml}
- python/{analytics,utils,serial,simulation}
- dashboard/{app.py,components,pages}
- ml/{inference,training,models,datasets}
- assets/{diagrams,screenshots,demos}
- tests/
- scripts/

## Phase 3 Naming Normalization

Canonical docs renamed to lowercase underscore format:
- docs/executive_summary.md
- docs/full_study.md
- docs/workflow_guide.md
- docs/migration_blueprint.md

## Phase 4 Interlinking

- Root README updated to normalized architecture and doc links.
- Consolidated docs updated to normalized canonical references.
- Dashboard wrapper added at dashboard/app.py and launcher updated to use it.
- Firmware root include wrappers added to keep main.ino include paths unchanged.

## Phase 5 Cleanup Actions

Archived:
- LOGS/replay_outputs -> LOGS/archive/replay_outputs

Removed:
- All __pycache__ directories
- Legacy uppercase master-doc filenames after references were migrated

## Phase 6 Professionalization Status

Completed:
- Modular folder boundaries
- Runtime-safe compatibility wrappers
- Normalized naming for source-of-truth docs
- Documentation and launcher interlinking

Pending future pass:
- Deeper migration of remaining src modules into python/ subpackages with wrappers retained.
- Migration of validation scripts into tests/ with wrappers.
