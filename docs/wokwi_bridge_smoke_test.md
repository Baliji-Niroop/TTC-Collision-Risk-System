# Wokwi Bridge Smoke Test

Use this quick check to confirm the bridge can validate and forward canonical packets.

## Required environment

`run_wokwi_bridge.bat` uses these variables:

- `WOKWI_SERIAL_WS_URL` (optional): websocket source URL for websocket mode.
- `WOKWI_BRIDGE_SERIAL_OUT` (optional): COM port the bridge writes canonical packets to.
- `WOKWI_READER_PORT` (optional): paired COM port read by `serial_reader.py` when stack launch is enabled.

If none are set, the batch file prints a warning and still starts the bridge.

## Batch launcher behavior

```cmd
run_wokwi_bridge.bat
```

Current behavior:

- Uses `.venv\Scripts\python.exe` when available, otherwise falls back to `ttc_env\Scripts\python.exe`.
- Sets `TTC_DASHBOARD_DEFAULT_MODE=Live Log`.
- Starts `bridge\wokwi_serial_bridge.py --launch-stack`.
- Bridge runs protocol preflight (`validation\protocol_contract_test.py`) before processing input.

## Practical stdin smoke mode (safe, no websocket)

Use this mode to test packet acceptance without launching reader or dashboard:

```cmd
if exist .\.venv\Scripts\python.exe (
	echo 1000,120,30,2.40,2.20,2,0.85 | .\.venv\Scripts\python.exe bridge\wokwi_serial_bridge.py --source stdin --no-launch-stack
) else (
	echo 1000,120,30,2.40,2.20,2,0.85 | .\ttc_env\Scripts\python.exe bridge\wokwi_serial_bridge.py --source stdin --no-launch-stack
)
```

Expected checks:

- Protocol preflight passes.
- Bridge logs `Forwarded canonical packet`.
- `LOGS\live_data.txt` contains the canonical row.
