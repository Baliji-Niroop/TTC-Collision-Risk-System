# Final Report Figure Package

This is the final figure set for report and faculty presentation.

1. Software architecture
   - Source: `docs/diagrams/` architecture diagram, or regenerate from system modules.
2. Protocol flow
   - Source: strict canonical path from firmware packet to validators and dashboard.
3. Wokwi virtual hardware
   - Source: Wokwi canvas screenshot showing ESP32, HC-SR04, OLED, LEDs, buzzer.
   - Place the exported image in `assets/screenshots/`.
4. Bridge workflow
   - Source: flow image from `bridge/wokwi_serial_bridge.py` path:
     Wokwi stream -> strict validation -> COM/live log -> serial reader/dashboard.
5. TTC live chart
   - Source: `validation/outputs/demo_evidence/<session>/confidence_ttc_trends.png` (TTC panel).
6. Confidence chart
   - Source: `validation/outputs/demo_evidence/<session>/confidence_ttc_trends.png` (confidence panel).
7. Event timeline
   - Source: `validation/outputs/demo_evidence/<session>/alert_timeline.csv` visualized in spreadsheet or plotting tool.
8. Baseline comparison
   - Source: `validation/outputs/demo_evidence/<session>/baseline_comparison.json` with bar chart export.

## Recommended caption style

- Use one-line captions with what, why, and result.
- Include sample count and timestamp for every empirical figure.