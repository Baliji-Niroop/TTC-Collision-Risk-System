# Demo Evidence Export Checklist

Use this checklist each time you package faculty-demo evidence.

## A. Capture session evidence

1. Start Wokwi simulation and verify OLED, LEDs, and buzzer are active.
2. Start bridge stack with `run_wokwi_bridge.bat`.
3. Capture evidence session:

```powershell
& .\ttc_env\Scripts\python.exe validation\capture_demo_evidence.py --source stdin --duration-sec 30
```

4. Confirm new folder exists under `validation/outputs/demo_evidence/` with:
   - `canonical_session.csv`
   - `risk_distribution.json`
   - `confidence_trend.csv`
   - `ttc_trend.csv`
   - `alert_timeline.csv`
   - `session_summary.json`

## B. Required screenshots

1. Wokwi OLED and LEDs screenshot.
2. Dashboard live panel screenshot (current metrics and risk banner).
3. Dashboard event log screenshot with mixed SAFE, WARNING, CRITICAL rows.
4. Replay confusion matrix screenshot from `validation/outputs/confusion_matrix.png`.
5. Replay vs Wokwi comparison screenshot after running:

```powershell
& .\ttc_env\Scripts\python.exe validation\compare_wokwi_baseline.py --input validation\outputs\demo_evidence\<session>\canonical_session.csv --output validation\outputs\demo_evidence\<session>\baseline_comparison.json
```

## C. Chart exports

1. Keep generated `confidence_ttc_trends.png`.
2. Keep generated `risk_distribution.png`.
3. Keep existing replay artifacts:
   - `validation/outputs/confusion_matrix.png`
   - `validation/outputs/scenario_summary.png`
   - `validation/outputs/timeline_summary.png`

## D. Quality gate before publishing

1. `session_summary.json` rows captured >= 30.
2. Risk distribution includes all three classes at least once for demo runs.
3. Confidence values remain in [0.0, 1.0].
4. No malformed-packet bursts in bridge logs.
5. Baseline comparison JSON is attached.