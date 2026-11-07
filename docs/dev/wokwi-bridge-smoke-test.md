# Wokwi and Serial Bridge

The repository includes a Wokwi circuit definition, but not compiled firmware
artifacts or a captured simulator run.

## Prepare Wokwi firmware

`wokwi.toml` expects these local files:

```text
build/TTC.ino.bin
build/TTC.ino.elf
```

The root `TTC.ino` wrapper includes `firmware/main.ino`. Compile the wrapper
with the ESP32 Arduino toolchain, export its binary and ELF files, and place
them at the paths above. The `build/` directory is ignored by Git.

## Connect the bridge

`run_wokwi_bridge.bat` starts `bridge/wokwi_serial_bridge.py`. Configure the
Wokwi WebSocket URL and paired virtual serial ports as needed:

- `WOKWI_SERIAL_WS_URL`: optional WebSocket URL.
- `WOKWI_BRIDGE_SERIAL_OUT`: bridge write port.
- `WOKWI_READER_PORT`: paired, different port read by `serial_reader.py`.

The launcher can start the reader/dashboard stack when the ports are configured.
See [usage](../usage.md) for user-facing run instructions.

## Packet smoke test

This command checks the bridge's stdin packet path without a Wokwi session:

```bash
echo 1000,120,30,2.40,2.20,2,0.85 | python bridge/wokwi_serial_bridge.py --source stdin --no-launch-stack
```

The bridge runs the protocol preflight and reports whether it accepted the
canonical packet. It does not prove that the Wokwi simulation or virtual COM
pair is working.

## Related documentation

- [Serial protocol](../serial_protocol.md)
- [Simulation validation checklist](simulation-validation-checklist.md)
- [Hardware wiring](../../hardware/wiring_guide.md)
