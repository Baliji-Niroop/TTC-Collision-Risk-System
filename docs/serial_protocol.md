# Serial Telemetry Protocol

This document defines the packet format currently expected by the Python side of the TTC project.

If ESP32 firmware is written or updated it should match this format unless the Python parser is intentionally changed at the same time.

## Packet format

Each serial message must be one line of CSV with exactly 7 fields:

```
timestamp_ms,distance_cm,speed_kmh,ttc_basic,ttc_ext,risk_class,confidence
```

Example:

```
1250,184.50,22.0,3.02,2.88,0,0.94
```

## Field definitions

| Position | Field | Type | Unit | Meaning |
|----------|-------|------|------|---------|
| 1 | `timestamp_ms` | float or integer | ms | Sample timestamp in milliseconds |
| 2 | `distance_cm` | float | cm | Current obstacle distance |
| 3 | `speed_kmh` | float | km/h | Current closing speed |
| 4 | `ttc_basic` | float | s | TTC using the constant-speed assumption |
| 5 | `ttc_ext` | float | s | TTC using the extended deceleration-aware estimate |
| 6 | `risk_class` | integer | — | `0` = SAFE, `1` = WARNING, `2` = CRITICAL |
| 7 | `confidence` | float | 0.0–1.0 | Confidence score for the current reading |

## Parsing rules used by Python

The current Python parser expects:

- A comma-separated line.
- Exactly 7 fields.
- Numeric values in every field.
- `risk_class` parseable as an integer.
- `confidence` between `0.0` and `1.0`.

Rows may be rejected if they contain:

- The wrong number of fields.
- Invalid numeric formatting.
- Negative distance.
- Impossible TTC values.
- Unrealistic speed values.
- Invalid confidence values.

## Current threshold conventions

The default TTC thresholds in the Python code are:

- **CRITICAL:** TTC ≤ 1.5 s.
- **WARNING:** 1.5 < TTC ≤ 3.0 s.
- **SAFE:** TTC > 3.0 s.

If the ESP32 computes `risk_class` locally it should follow the same thresholds unless the project is being updated everywhere together.

## Recommended firmware output rules

- Send one complete line per reading.
- End each packet with a newline.
- Keep field order fixed.
- Keep units fixed.
- Do not add labels such as `dist=` or `ttc=`.
- Do not add extra commas or extra fields.
- If a value is unavailable, decide on a fallback convention before changing the protocol.

## Recommended sampling guidance

The software side is currently configured around a sub-second monitoring loop. A practical starting point is one packet every 200–500 ms.

That is fast enough for dashboard updates without producing unnecessary serial noise during early testing.

## Firmware handoff checklist

Before the first ESP32 test, confirm:

1. The board sends exactly 7 CSV values per line.
2. The baud rate matches the Python configuration.
3. Distances are in centimetres.
4. Speed is in km/h.
5. `risk_class` uses `0`, `1`, or `2` only.
6. `confidence` stays in the range `0.0` to `1.0`.

## Related files

- `src/serial_reader.py`
- `src/validators.py`
- `src/config.py`
- `README.md`
