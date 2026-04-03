# Workflow & Implementation Guide

## 1. Daily Development Workflow

### 1.1 Fast run (simulator + dashboard)
- Use `run_dashboard.bat`, or run manually:
  - `python src/serial_simulator.py`
  - `streamlit run src/dashboard.py --server.headless true`

### 1.2 Wokwi bridge workflow
- Use `run_wokwi_bridge.bat` for bridge stack launch.
- Ensure packet stream remains canonical.

### 1.3 Validation workflow
- Protocol contract check:
  - `python validation/protocol_contract_test.py`
- Synthetic evaluation:
  - `python validation/evaluate_synthetic.py`
- Baseline comparison:
  - `python validation/compare_wokwi_baseline.py --input LOGS/session_YYYYMMDD_HHMMSS.csv`

## 2. Implementation Rules

### 2.1 Contract rule (non-negotiable)
Every packet must contain exactly 7 fields in canonical order.

### 2.2 Threshold rule
Keep risk thresholds synchronized in:
- `src/config.py`
- `firmware/config.h`

### 2.3 ML resilience rule
Never require model presence for runtime operation. Always preserve TTC fallback.

## 3. Practical Folder Standardization

Current standardized top-level structure includes:
- `firmware/`
- `python/`
- `simulation/`
- `ml/`
- `dashboard/`
- `docs/`
- `assets/`
- `validation/`

Implementation note:
- Runtime Python modules remain in `src/` for compatibility with existing scripts.
- `python/`, `dashboard/`, and `ml/` currently act as architecture anchors.

## 4. Firmware Bring-up Checklist
1. Replace placeholder reads in `firmware/sensors.h` with real sensor drivers.
2. Verify output packet order and units after each change.
3. Confirm TTC and risk values remain stable under expected inputs.

## 5. Serial Integration Checklist
1. Run `python src/serial_reader.py --list` and identify target port.
2. Start reader with `--port` and verify updates in `LOGS/live_data.txt`.
3. Open dashboard and confirm stable rendering in Live Log/Serial modes.

## 6. Validation Checklist
1. Replay sample sessions and inspect metrics consistency.
2. Validate protocol strictness before and after firmware changes.
3. Archive outputs for reproducibility (`validation/outputs/`).

## 7. Handoff/Review Walkthrough
1. Confirm canonical contract and thresholds first.
2. Show simulator workflow.
3. Show Wokwi bridge workflow.
4. Show serial ingestion path.
5. Show validation output and known open hardware gaps.

## 8. Final Implementation Baseline
A change is considered complete only when:
- Contract remains strict.
- Dashboard remains stable in all modes.
- Validation scripts pass.
- Documentation in the three master docs remains accurate.

## 9. Phase-2 Migration Blueprint
For staged runtime-safe module migration, use:

- `docs/migration_blueprint.md`
