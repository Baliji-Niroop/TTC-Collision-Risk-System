# Serial Telemetry Protocol

This document defines the canonical telemetry contract used by firmware and Python runtime components.

## Contract Status

- The protocol is frozen to exactly 7 CSV fields.
- Field names, order, and units are mandatory.
- Legacy aliases are not accepted.

## Packet Format

Each message must be one line with exactly 7 comma-separated values:

```text
timestamp_ms,distance_cm,speed_kmh,ttc_basic,ttc_ext,risk_class,confidence
```

Example:

```text
1250,184.50,22.0,3.02,2.88,0,0.94
```

## Field Definitions

| Position | Field | Type | Unit | Description |
| --- | --- | --- | --- | --- |
| 1 | `timestamp_ms` | float or int | ms | Sample timestamp |
| 2 | `distance_cm` | float | cm | Obstacle distance |
| 3 | `speed_kmh` | float | km/h | Host or closing speed |
| 4 | `ttc_basic` | float | s | Constant-speed TTC estimate |
| 5 | `ttc_ext` | float | s | Extended TTC estimate |
| 6 | `risk_class` | int | n/a | 0=safe, 1=warning, 2=critical |
| 7 | `confidence` | float | 0.0-1.0 | Confidence score |

## Python Parsing Rules

Accepted rows must satisfy all rules below:

- Exactly 7 fields.
- Numeric values in all positions.
- `risk_class` parseable as integer.
- `confidence` in range `[0.0, 1.0]`.
- No alias field names.

Rejected row examples:

- Wrong field count.
- Invalid numeric formatting.
- Negative distance.
- Invalid confidence value.
- Protocol alias usage.

## Firmware Emitter Requirement

Firmware output must preserve exact order and newline termination:

```text
timestamp_ms,distance_cm,speed_kmh,ttc_basic,ttc_ext,risk_class,confidence\n
```

Reference: `firmware/config/serial_protocol.h` and `firmware/main.ino`.

## Threshold Conventions

- Critical: TTC <= 1.5 seconds
- Warning: 1.5 < TTC <= 3.0 seconds
- Safe: TTC > 3.0 seconds

If local firmware classification is enabled, values must remain synchronized with `src/config.py`.

## Firmware Handoff Checklist

1. Device emits exactly 7 values per line.
2. Baud rate matches Python reader configuration.
3. Distance unit is centimeters.
4. Speed unit is km/h.
5. `risk_class` only uses 0, 1, or 2.
6. `confidence` stays within 0.0 to 1.0.

## Related Files

- `src/telemetry_schema.py`
- `src/serial_reader.py`
- `src/validators.py`
- `src/config.py`
- `src/serial_simulator.py`
- `src/replay_runner.py`
- `validation/evaluate_synthetic.py`
- `firmware/config/serial_protocol.h`

## Sync Impact

Any protocol change requires synchronized updates in:

- `firmware/main.ino`
- `bridge/wokwi_serial_bridge.py`
- `src/serial_reader.py`
- `src/telemetry_schema.py`
- `src/validators.py`
- `validation/protocol_contract_test.py`
- `docs/serial_protocol.md`
