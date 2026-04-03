# Wokwi Bridge Smoke Test

This is the shortest Windows path for verifying the Wokwi ESP32 simulation against the strict TTC pipeline.

## Prerequisites

- Wokwi project open with the TTC `diagram.json` and `sketch.ino`.
- Python environment available from `ttc_env`.
- A virtual COM pair installed on Windows, such as com0com or VSPE.

## Recommended COM layout

- Bridge writes to `COM9`.
- `serial_reader.py` reads from `COM8`.
- `COM8` and `COM9` must be the paired endpoints of the same virtual COM bridge.

## One-command run

1. Set `WOKWI_SERIAL_WS_URL` if you are using a websocket stream from Wokwi, or pipe the Wokwi serial output into the bridge stdin.
2. Set `WOKWI_BRIDGE_SERIAL_OUT=COM9`.
3. Set `WOKWI_READER_PORT=COM8`.
4. Double-click `run_wokwi_bridge.bat`.

The batch file starts:

- the Wokwi bridge
- `serial_reader.py`
- the Streamlit dashboard in Live Log mode

## What to verify

- SAFE rows appear in the dashboard when the simulated distance is large.
- WARNING rows appear as the obstacle approaches the warning threshold.
- CRITICAL rows appear below the critical TTC threshold.
- `confidence` stays between 0.0 and 1.0.
- The line chart and metrics update every 200 ms packet cycle.
- The OLED, LEDs, buzzer, and serial text all agree on the current risk class.

## Strict validation loop

- The bridge runs `validation/protocol_contract_test.py` before starting the stack.
- Each incoming packet is validated through `validators.validate_csv_line()`.
- Any malformed packet is rejected and logged loudly.

## Baseline comparison

After a short run, compare the captured CSV against the replay baseline:

```powershell
& .\ttc_env\Scripts\python.exe validation\compare_wokwi_baseline.py --input LOGS\session_YYYYMMDD_HHMMSS.csv
```

Check that the SAFE, WARNING, and CRITICAL percentages are in the same general shape as the replay summary and that confidence trends remain stable.