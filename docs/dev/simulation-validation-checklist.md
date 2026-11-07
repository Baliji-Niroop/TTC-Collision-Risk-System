# Simulation Validation Checklist

Use this checklist after a firmware, bridge, or TTC logic change. It only
validates the commands actually run; synthetic tests do not replace physical
hardware testing.

## Prerequisites

- Install `requirements.txt` and `requirements-dev.txt`.
- Keep the seven-field packet contract unchanged.
- For Wokwi, prepare the build artifacts listed in
  [the Wokwi guide](wokwi-bridge-smoke-test.md).

## Python checks

From the repository root, run:

```bash
python -m pytest
python validation/protocol_contract_test.py
python src/main.py --demo
```

For model metrics, train first and then evaluate:

```bash
python ml/training/train_model.py
python validation/evaluate_synthetic.py
```

Confirm that the reported train and test scenario names are disjoint. The
evaluation prints Random Forest and TTC-rule baseline metrics separately and
generates `results/confusion_matrix.png` from the held-out scenarios.

## Bridge packet smoke test

This stdin check exercises the bridge's packet path without starting Wokwi:

```bash
echo 1000,120,30,2.40,2.20,2,0.85 | python bridge/wokwi_serial_bridge.py --source stdin --no-launch-stack
```

## Dashboard stack

On Windows, run `run_dashboard.bat`. It starts the telemetry simulator and
dashboard. Confirm that the health check succeeds and the dashboard displays
changing telemetry.
