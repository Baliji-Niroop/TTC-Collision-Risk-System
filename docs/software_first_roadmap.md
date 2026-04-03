# Software-First Completion Roadmap

Target: keep the repo release-ready while using the Wokwi validation as the bridge from software-first development to physical hardware bring-up.

## 1. Freeze the telemetry contract

1. Keep `timestamp_ms,distance_cm,speed_kmh,ttc_basic,ttc_ext,risk_class,confidence` as the only canonical packet.
2. Update every producer and consumer to use the shared helpers in `src/telemetry_schema.py`.
3. Keep `docs/serial_protocol.md` and `docs/wokwi_hardware_validation.md` as the human-readable protocol references.

## 2. Build offline validation coverage

1. Generate `dataset/synthetic_ttc_validation.csv` with the six required scenarios.
2. Run `validation/evaluate_synthetic.py` to produce confusion matrix, classification report, critical recall, and false alarm rate.
3. Save the resulting plots under `validation/outputs/` and review whether each scenario behaves as expected.
4. Keep `validation/protocol_contract_test.py` as the strict schema gate.

## 3. Exercise the full runtime pipeline without hardware

1. Replay saved sessions through `src/replay_runner.py`.
2. Validate the path through validators, alerts, parser, ML predictor, and analytics.
3. Compare replay output against the dashboard display and session CSV export.
4. Preserve the replay outputs as report evidence.

## 4. Finish the firmware handoff package

1. Keep the firmware in `firmware/` aligned with the canonical packet contract.
2. Confirm the firmware emits the canonical packet format over Serial.
3. Match the Wokwi `Dxx` pin naming convention in the physical wiring plan.
4. Add the final sensor implementation only after procurement.

## 5. Make report assets reproducible

1. Maintain Mermaid sources in `docs/diagrams/` for architecture, protocol, flow, and state machine views.
2. Use the validation script outputs as report-ready evidence for model quality.
3. Use replay charts as evidence that the end-to-end software path is stable.
4. Store presentation screenshots in `assets/screenshots/`.

## 6. Polish the software deliverables

1. Update README and status documents to reflect the frozen schema and Wokwi validation.
2. Normalize any remaining column names or field aliases in the Python codebase.
3. Package the project so that the first hardware test only needs the board and sensor, not code surgery.

## 7. Hardware-ready exit criteria

The software phase is effectively complete when these are true:

1. The dashboard works in simulator, live log, replay, and serial modes.
2. The synthetic dataset pipeline produces repeatable metrics and plots.
3. The firmware builds cleanly and prints valid packets.
4. The serial reader accepts canonical packets without schema translation.
5. The replay runner exercises the same validation and alert path used by live data.
6. The Wokwi validation guide remains the reference for the physical wiring plan.
