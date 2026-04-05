# Wokwi Hardware Validation

This is the official virtual hardware validation reference for the TTC Collision Risk Prediction System.

The Wokwi build is the release-quality proof point for the embedded side of the project. It validates the ESP32 wiring convention, the telemetry contract, and the risk-response behavior before any physical hardware is purchased.

## Validated hardware map

The Wokwi `esp32-devkit-v1` part uses `Dxx` labels in `diagram.json`. The validated mapping is:

- HC-SR04 `VCC` -> `VIN`
- HC-SR04 `GND` -> `GND`
- HC-SR04 `TRIG` -> `D5`
- HC-SR04 `ECHO` -> `D18`
- OLED `VCC` -> `3V3`
- OLED `GND` -> `GND`
- OLED `SDA` -> `D21`
- OLED `SCL` -> `D22`
- SAFE LED 1 -> `D25`
- SAFE LED 2 -> `D26`
- WARNING LED 1 -> `D27`
- WARNING LED 2 -> `D14`
- CRITICAL LED -> `D12`
- Buzzer positive -> `D32`
- Buzzer negative -> `GND`

## What was verified

- Live TTC values render on the OLED.
- SAFE, WARNING, and CRITICAL LEDs switch at the correct thresholds.
- The buzzer activates on critical events.
- The obstacle performs the automatic closing sweep used for demo mode.
- The serial output stays locked to the canonical seven-field packet.
- The Python bridge and reader reject legacy or malformed packets.

## Risk thresholds

- SAFE: TTC > 3.0 s
- WARNING: 1.5 s < TTC <= 3.0 s
- CRITICAL: TTC <= 1.5 s

## Expected OLED behavior

- SAFE: normal monitoring state with a comfortably high TTC.
- WARNING: caution state when TTC falls below 3.0 s.
- CRITICAL: alarm state when TTC reaches 1.5 s or lower.

## Reproduction steps

1. Open the Wokwi project using `diagram.json` and `sketch.ino`.
2. Start the ESP32 simulation.
3. Run `run_wokwi_bridge.bat` on Windows.
4. Confirm the bridge protocol preflight passes.
5. Watch the dashboard in Live Log mode or ESP32 Serial mode.
6. Sweep the obstacle through SAFE, WARNING, and CRITICAL ranges and confirm the OLED, LEDs, buzzer, and packet stream remain synchronized.

## Why auto sweep is used

Auto sweep gives a repeatable way to demonstrate all three risk states in one session. It also makes it easy to capture screenshots, replay comparisons, and faculty demo footage without manual timing noise.

## Evidence paths

- Wokwi source: `diagram.json`
- Firmware source: `sketch.ino` and `firmware/`
- Telemetry contract: `docs/serial_protocol.md`
- Dashboard integration: `src/dashboard.py`
- Validation reports: `validation/outputs/`
- Demo evidence bundles: `validation/outputs/demo_evidence/`
- Screenshot placeholders: `assets/screenshots/`
