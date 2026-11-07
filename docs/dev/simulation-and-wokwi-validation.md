# Simulation and Wokwi Validation

The repository includes a Wokwi circuit definition, but compiled firmware
artifacts are local build outputs and a captured Wokwi run is not checked in.
These checks validate the Python pipeline; they do not replace physical
hardware testing.

## Run the local checks

From the repository root, install `requirements.txt` and
`requirements-dev.txt`, then run:

```bash
python -m pytest
python validation/protocol_contract_test.py
python validation/pin_validator.py
python src/main.py --demo
```

To regenerate held-out model results, train first and then evaluate:

```bash
python ml/training/train_model.py
python validation/evaluate_synthetic.py
```

The split keeps whole scenarios apart. The checked-in labels are generated
from TTC rules; see [evaluation results](../../results/README.md).

## Check the bridge packet path

This stdin smoke test validates one canonical packet without starting Wokwi:

```bash
echo 1000,120,30,2.40,2.20,2,0.85 | python bridge/wokwi_serial_bridge.py --source stdin --no-launch-stack
```

An accepted packet confirms the bridge's local packet path only. It does not
verify Wokwi, USB, or virtual serial ports.

## Capture simulator evidence

To save a local evidence bundle from a Wokwi serial WebSocket session:

```bash
python validation/capture_demo_evidence.py --source websocket --ws-url "YOUR_WOKWI_WEBSOCKET_URL" --duration-sec 25 --min-rows 30
```

Replace the URL placeholder with the WebSocket URL for your Wokwi session.
The script writes CSV, JSON, and plot outputs beneath
`validation/outputs/demo_evidence/`. These are generated artifacts and should
not be committed.

## Prepare and connect Wokwi

`wokwi.toml` expects these local files:

```text
build/TTC.ino.bin
build/TTC.ino.elf
```

The root `TTC.ino` wrapper includes `firmware/main.ino`. Compile the wrapper
with the ESP32 Arduino toolchain and place its exported binary and ELF files
at the paths above. The `build/` directory is ignored by Git.

`run_wokwi_bridge.bat` starts `bridge/wokwi_serial_bridge.py`. Configure the
WebSocket URL and paired virtual serial ports as needed:

- `WOKWI_SERIAL_WS_URL`: optional WebSocket URL.
- `WOKWI_BRIDGE_SERIAL_OUT`: bridge write port.
- `WOKWI_READER_PORT`: paired, different port read by `serial_reader.py`.

The launcher can start the reader/dashboard stack when the ports are
configured. See [usage](../usage.md) and [the serial protocol](../serial_protocol.md).
For hardware pin assignments, see the [wiring guide](../../hardware/wiring_guide.md).
