# Project map

Run commands from the repository root.

| Area | Key files |
|---|---|
| Python entry points | `src/main.py`, `src/dashboard.py` |
| Telemetry ingestion | `src/serial_reader.py`, `src/serial_simulator.py`, `bridge/wokwi_serial_bridge.py` |
| Packet parsing and validation | `src/telemetry_schema.py`, `src/validators.py` |
| Firmware | `firmware/main.ino`, `firmware/pinmap.h`, `firmware/config/` |
| Training and inference | `ml/training/`, `ml/inference/`, `MODELS/` (generated local artifacts) |
| Dataset | `data/synthetic_ttc_validation.csv` |
| Tests and validation | `tests/`, `validation/` |
| User documentation | `README.md`, `docs/`, `hardware/` |

`LOGS/`, `MODELS/*.pkl`, and `validation/outputs/` contain local generated artifacts and are not committed.

The telemetry contract is defined in `firmware/config/serial_protocol.h` and `src/telemetry_schema.py`. Python and firmware risk thresholds are in `src/config.py` and `firmware/config/config.h`.
