# Simulation Validation Checklist

Use this checklist after any firmware, bridge, or TTC logic change.

## Goal

Confirm the system remains safe, protocol-compliant, and operational in simulation.

## Pre-checks

- [ ] Firmware compiles and binary artifacts are available for Wokwi use.
- [ ] Python environment is ready (.venv or ttc_env).
- [ ] Protocol contract is unchanged (7 fields, fixed order).

## 1) Protocol Contract

Run:

```bat
ttc_env\Scripts\python.exe validation\protocol_contract_test.py
```

Expected:

- [ ] Passes with no schema/order violations.
- [ ] Field order is exactly:
  timestamp_ms, distance_cm, speed_kmh, ttc_basic, ttc_ext, risk_class, confidence

## 2) Bridge Smoke

Run:

```bat
echo 1000,120,30,2.40,2.20,2,0.85 | ttc_env\Scripts\python.exe bridge\wokwi_serial_bridge.py --source stdin --no-launch-stack
```

Expected:

- [ ] Preflight protocol check passes.
- [ ] Canonical packet is forwarded.
- [ ] No parse or validation errors.

## 3) Dashboard Stack

Run:

```bat
run_dashboard.bat
```

Expected:

- [ ] Dashboard starts without import/runtime failures.
- [ ] Live values render and refresh correctly.
- [ ] Risk class transitions are visible.

## 4) Safety Behavior

Validate these decision outcomes:

- [ ] Safe scenario: TTC > 3.0s -> safe classification.
- [ ] Warning scenario: 1.5s < TTC <= 3.0s -> warning classification.
- [ ] Critical scenario: TTC <= 1.5s -> critical classification.
- [ ] Invalid packet input is rejected safely (no crash).

## 5) Regression Checks

Run:

```bat
ttc_env\Scripts\python.exe validation\evaluate_synthetic.py
```

Expected:

- [ ] Script completes successfully.
- [ ] Output artifacts are generated under validation/outputs when expected.

## Pass Criteria

A change is simulation-validated only when all sections above pass.

## Recommended Task Path

For repeatable enforcement, run `Quality: Full Gate` from VS Code tasks.
