# Hardware-Ready Strict Schema Report

Date: 2026-04-03

## Strict schema compliance

- Canonical telemetry contract is enforced as the single schema:
  - `timestamp_ms,distance_cm,speed_kmh,ttc_basic,ttc_ext,risk_class,confidence`
- Legacy alias compatibility paths were removed from runtime parsing and inference.
- Validator strict mode now rejects:
  - wrong field count
  - non-numeric/header-like packet rows
  - schema mismatch in parsed row dictionaries
  - legacy alias tokens (for example `risk_phys`, `v_closing_kmh`, `ttc_basic_s`, `speed_alias`)

## Modules touched

- `src/validators.py`
- `src/ml_inference.py`
- `src/dashboard.py`
- `src/safety_features.py` (comment terminology cleanup)
- `firmware/serial_protocol.h`
- `docs/serial_protocol.md`
- `validation/protocol_contract_test.py` (new)
- `bridge/wokwi_serial_bridge.py` (new)
- `run_wokwi_bridge.bat` (new)
- `requirements.txt` (websocket bridge dependency)

## Breakages found and fixed

- Dashboard retained old event-log columns (`ttc_basic_s`, `ttc_ext_s`, `confidence_%`) after canonical freeze.
  - Fixed by using canonical fields in the event table formatting path.
- Dashboard parser had a fallback parse path after validation.
  - Fixed by making `validate_csv_line` authoritative in strict mode.
- ML inference still accepted legacy alias fallback for risk class.
  - Fixed by removing `risk_phys` fallback.

## Wokwi bridge stage

- Added a Windows bridge layer that can ingest Wokwi serial output from a websocket stream or stdin pipe.
- Added strict packet preflight on startup by running `validation/protocol_contract_test.py` before the bridge stack comes up.
- Added COM-forwarding support so a virtual COM pair can feed `serial_reader.py` exactly like a real ESP32 device.
- Added a Windows runner that starts the bridge, serial reader, and dashboard together in Live Log mode.

## Evidence packaging stage

- Added `validation/capture_demo_evidence.py` to produce a reproducible evidence bundle from live bridge sessions.
- Added capture/export checklist and presentation packaging docs:
  - `docs/evidence_capture_checklist.md`
  - `docs/report_figure_package.md`
  - `docs/demo_assets.md`
- Evidence output now includes canonical CSV, distribution JSON, confidence/TTC trends, alert timeline, and session summary JSON.

## Smoke-test path

1. Start Wokwi with the ESP32 simulation project.
2. Run `run_wokwi_bridge.bat`.
3. Confirm the bridge logs rejected malformed packets loudly and forwards valid canonical packets unchanged.
4. Confirm `serial_reader.py` writes `LOGS/live_data.txt`.
5. Open the dashboard and verify Live Log mode is updating.
6. Sweep the HC-SR04 distance through SAFE, WARNING, and CRITICAL ranges and confirm the OLED, LEDs, buzzer, and serial text all stay synchronized.

## Recheck results

- Synthetic dataset regeneration: PASS (610 rows generated)
- Synthetic evaluation + confusion matrix: PASS
  - Accuracy: `0.9934`
  - Critical recall: `0.9979`
  - False alarm rate: `0.00735`
- Replay runner: PASS
  - Rows processed: `238`
  - Mean confidence: `0.9535`
- Protocol contract tests: PASS (`6/6`)
- Bridge dry-run smoke test: PASS (canonical stdin packet forwarded after protocol preflight)

## Hardware bring-up confidence

- Confidence level: High for telemetry-contract readiness and virtual integration.
- Rationale:
  - Single canonical schema enforced in parser, validator, dashboard pipeline, and firmware emitter contract.
  - Offline replay and validation still pass after strict cleanup.
  - Wokwi bridge path now exercises the same strict parser/validation loop before any physical hardware is purchased.

## Final completion percentage

- Software-first completion (pre-hardware): **96%**
- Overall project completion (including hardware integration pending): **84%**

## Physical tasks remaining

- Procure the ESP32 DevKit V1.
- Procure the HC-SR04 sensor.
- Procure or confirm the OLED SSD1306, LEDs, buzzer, and wiring materials.
- Build the physical wiring harness and verify 3.3V/5V safety.
- Validate real ultrasonic distance accuracy against measured ground truth.
- Run live real-ESP32 serial smoke test through the same strict bridge/reader path.
- Measure TTC threshold crossing timing and alert latency on physical hardware.
- Capture and compare a real hardware session against replay and Wokwi baselines.
