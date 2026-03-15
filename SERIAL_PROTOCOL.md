# Serial Telemetry Protocol

This document defines the packet format currently expected by the Python side of the TTC project.

If ESP32 firmware is written or updated, it should match this format unless the Python parser is intentionally changed at the same time.

## Packet Format

Each serial message must be one line of CSV with exactly 7 fields:

```text
timestamp_ms,distance_cm,speed_kmh,ttc_basic,ttc_ext,risk_class,confidence
```

Example:

```text
1250,184.50,22.0,3.02,2.88,0,0.94
```

## Field Definitions

| Position | Field | Type | Unit | Meaning |
| ---- | ---- | ---- | ---- | ---- |
| 1 | `timestamp_ms` | float or integer | ms | Sample timestamp in milliseconds |
| 2 | `distance_cm` | float | cm | Current obstacle distance |
| 3 | `speed_kmh` | float | km/h | Current closing speed |
| 4 | `ttc_basic` | float | s | TTC using the constant-speed assumption |
| 5 | `ttc_ext` | float | s | TTC using the extended deceleration-aware estimate |
| 6 | `risk_class` | integer | none | `0 = SAFE`, `1 = WARNING`, `2 = CRITICAL` |
| 7 | `confidence` | float | 0.0 to 1.0 | Confidence score for the current reading |

## Parsing Rules Used By Python

The current Python parser expects:

- a comma-separated line
- exactly 7 fields
- numeric values in every field
- `risk_class` parseable as an integer
- `confidence` between `0.0` and `1.0`

Rows may be rejected if they contain:

- the wrong number of fields
- invalid numeric formatting
- negative distance
- impossible TTC values
- unrealistic speed values
- invalid confidence values

## Current Threshold Conventions

The default TTC thresholds in the Python code are:

- `CRITICAL`: `ttc <= 1.5`
- `WARNING`: `1.5 < ttc <= 3.0`
- `SAFE`: `ttc > 3.0`

If the ESP32 computes `risk_class` locally, it should follow the same thresholds unless the project is being updated everywhere together.

## Recommended Firmware Output Rules

- Send one complete line per reading.
- End each packet with a newline.
- Keep field order fixed.
- Keep units fixed.
- Do not add labels such as `dist=` or `ttc=`.
- Do not add extra commas or extra fields.
- If a value is unavailable, decide on a fallback convention before changing the protocol.

## Recommended Sampling Guidance

The software side is currently configured around a sub-second monitoring loop. A practical starting point is one packet every `200-500 ms`.

That is fast enough for dashboard updates without producing unnecessary serial noise during early testing.

## Firmware Handoff Checklist

Before first ESP32 test, confirm:

1. The board sends exactly 7 CSV values per line.
2. The baud rate matches the Python configuration.
3. Distances are in centimeters.
4. Speed is in km/h.
5. `risk_class` uses `0`, `1`, or `2` only.
6. `confidence` stays in the range `0.0` to `1.0`.

## Related Files

- `PYTHON/serial_reader.py`
- `PYTHON/validators.py`
- `PYTHON/config.py`
- `README.md`
