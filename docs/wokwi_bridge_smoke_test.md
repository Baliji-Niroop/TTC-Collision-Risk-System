# Wokwi Bridge Smoke Test

Use this procedure to verify that the bridge validates and forwards canonical packets.

## Prerequisites

Before running Wokwi simulation, compile the firmware and export binaries:

1. Open Arduino IDE and load `TTC.ino`.
2. Select board: Tools > Board > ESP32 Dev Module.
3. Compile with Ctrl+R.
4. Export compiled binary.
5. Copy files:
	- `TTC.ino.bin` to `build/TTC.ino.bin`
	- `TTC.ino.elf` to `build/TTC.ino.elf`

The `wokwi.toml` will use these files. If they're missing, Wokwi cannot start.

## Environment Variables

`run_wokwi_bridge.bat` uses these variables:

- `WOKWI_SERIAL_WS_URL` (optional): WebSocket source URL for WebSocket mode.
- `WOKWI_BRIDGE_SERIAL_OUT` (optional): COM port the bridge writes canonical packets to.
- `WOKWI_READER_PORT` (optional): paired COM port read by `serial_reader.py` when stack launch is enabled.

If none are set, the launcher warns and still starts the bridge.

## Build Artifacts

If you run full Wokwi simulation with firmware binary loading, place exported files in `build/`:

- `build/TTC.ino.bin`
- `build/TTC.ino.elf`

The folder is ignored by git and can be recreated locally.

## Batch Launcher

```cmd
run_wokwi_bridge.bat
```

Behavior:

- Uses `.venv\Scripts\python.exe` when available, otherwise falls back to `ttc_env\Scripts\python.exe`.
- Sets `TTC_DASHBOARD_DEFAULT_MODE=Live Log`.
- Starts `bridge\wokwi_serial_bridge.py --launch-stack`.
- Bridge runs protocol preflight (`validation\protocol_contract_test.py`) before processing input.

## Stdin Smoke Mode

Use this mode to test packet acceptance without launching reader or dashboard:

```cmd
if exist .\.venv\Scripts\python.exe (
	echo 1000,120,30,2.40,2.20,2,0.85 | .\.venv\Scripts\python.exe bridge\wokwi_serial_bridge.py --source stdin --no-launch-stack
) else (
	echo 1000,120,30,2.40,2.20,2,0.85 | .\ttc_env\Scripts\python.exe bridge\wokwi_serial_bridge.py --source stdin --no-launch-stack
)
```

Expected result:

- Protocol preflight passes.
- Bridge logs `Forwarded canonical packet`.
- `LOGS\live_data.txt` contains the canonical row.

## Related Docs

- `docs/serial_protocol.md`
- `docs/simulation-validation-checklist.md`
- `hardware/wiring_guide.md`
