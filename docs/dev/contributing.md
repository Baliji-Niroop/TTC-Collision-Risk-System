# Contribution Conventions

Keep changes consistent with the existing structure and validate behavior
before opening a pull request.

## Repository layout

- `src/`: Python runtime, CLI, dashboard, and ingestion.
- `firmware/`: ESP32 firmware, configuration, and protocol.
- `bridge/`: serial and Wokwi integration.
- `ml/`: optional model training and inference.
- `data/`: the checked-in synthetic dataset and its provenance.
- `tests/` and `validation/`: automated tests and validation workflows.
- `docs/` and `hardware/`: user, developer, and wiring documentation.
- `LOGS/`, `MODELS/`, and `validation/outputs/`: local runtime artifacts.

Avoid new top-level directories when an existing area fits.

## Code and documentation

- Use `snake_case` for Python modules, functions, and variables; `PascalCase`
  for classes; and `UPPER_SNAKE_CASE` for constants.
- Keep shared paths and TTC thresholds in `src/config.py`.
- Keep firmware packet fields aligned with
  `firmware/config/serial_protocol.h` and `src/telemetry_schema.py`.
- Link to authoritative documentation instead of duplicating protocol,
  pin-map, or threshold definitions.
- Do not commit logs, local model files, or generated validation outputs.

## Validation

Install `requirements-dev.txt`, then run:

```bash
python -m pytest
python validation/protocol_contract_test.py
python validation/pin_validator.py
python src/main.py --demo
```

For model results, run `python ml/training/train_model.py` before
`python validation/evaluate_synthetic.py`. See the
[simulation and Wokwi validation guide](simulation-and-wokwi-validation.md).
