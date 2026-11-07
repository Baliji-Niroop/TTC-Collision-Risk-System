# Naming and Folder Policy

This policy is mandatory for all future contributions.

## Goals

- Keep repository layout stable and predictable.
- Keep runtime behavior and documentation easy to audit.
- Prevent naming drift and duplicate folder semantics.

## Folder Ownership Rules

- `src/`: Python runtime code only.
- `firmware/`: embedded firmware code and firmware config headers.
- `bridge/`: bridge and integration adapters for serial/Wokwi.
- `validation/`: end-to-end validation scripts and outputs.
- `tests/`: unit and integration tests.
- `docs/`: architecture, protocol, and workflow documentation.
- `hardware/`: physical wiring and assembly documentation.
- `data/`: checked-in synthetic dataset and its documentation.
- `MODELS/`: optional model artifacts only.
- `LOGS/`: runtime-generated logs only.

Do not create new top-level folders unless approved by maintainers.

## File Naming Rules

- Python files: `snake_case.py`.
- Markdown files: `kebab-case.md`.
- Batch scripts: `snake_case.bat` or existing launcher naming convention.
- Constants: `UPPER_SNAKE_CASE`.
- Classes: `PascalCase`.
- Functions and variables: `snake_case`.

## Documentation Rules

- Every markdown document must use clear section headings.
- Keep command examples copy-paste safe.
- Reference canonical files for protocol, pin mapping, and thresholds.
- Avoid historical notes that conflict with current source code.

## Configuration and Threshold Rules

- TTC threshold values must remain synchronized between:
  - `src/config.py`
  - `firmware/config/config.h`
- Do not hardcode threshold values in feature modules.

## Telemetry Contract Rules

The 7-field telemetry contract is frozen:

```text
timestamp_ms,distance_cm,speed_kmh,ttc_basic,ttc_ext,risk_class,confidence
```

No field aliases, reordering, or silent additions are allowed.

## Validation Gate

Install `requirements-dev.txt`, then run `python -m pytest`, `python validation/protocol_contract_test.py`, and `python src/main.py --demo`. To refresh model results, run `python ml/training/train_model.py` before `python validation/evaluate_synthetic.py`. A Wokwi run additionally needs the local build artifacts described in [the Wokwi guide](wokwi-bridge-smoke-test.md).

## Cleanup Rules

- Generated artifacts must not be committed.
- Keep placeholder markers (`.gitkeep`) for intentionally empty tracked folders.
- Remove stale docs that describe non-existent files or workflows.
