# Demo Assets For GitHub And Faculty Showcase

## Best screenshots to include

1. Wokwi hardware scene: ESP32 + HC-SR04 + OLED + LEDs + buzzer.
2. Dashboard live state with CRITICAL risk banner and current TTC.
3. Dashboard event log table with mixed risk classes.
4. Confusion matrix image: `validation/outputs/confusion_matrix.png`.
5. Evidence trend chart: `validation/outputs/demo_evidence/<session>/confidence_ttc_trends.png`.
6. Risk distribution chart: `validation/outputs/demo_evidence/<session>/risk_distribution.png`.
7. Screenshot placeholders in `assets/screenshots/`.

## GIF or video capture flow

1. Start Wokwi simulation.
2. Start `run_wokwi_bridge.bat`.
3. Capture 20 to 30 seconds showing:
   - Wokwi distance change
   - OLED risk state
   - dashboard risk banner + trend chart
   - event log updates
4. Save one short GIF (5 to 8 seconds) and one full MP4 (20 to 30 seconds).
5. Add a timestamped filename, for example `ttc_demo_2026-04-03.mp4`.

## README badge section

Use a compact status badge block near the top:

- `Protocol: Canonical Strict`
- `Validation: Replay + Wokwi Evidence`
- `Bridge: Windows Ready`
- `Status: Pre-Hardware Demo Complete`

## Demo proof order

Follow this exact order in GitHub README and faculty slides:

1. Canonical protocol freeze evidence.
2. Synthetic replay and confusion matrix evidence.
3. Wokwi virtual hardware screenshot.
4. Bridge workflow and strict validator gate.
5. Live dashboard screenshot and event timeline.
6. Replay vs Wokwi comparison summary.
7. Final pre-procurement status and physical-next-step list.