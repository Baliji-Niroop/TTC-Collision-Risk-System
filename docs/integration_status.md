# Hardware Integration Status

This file tracks the hardware-facing part of the TTC project separately from the software prototype.

## Current position

Python-side support is mostly ready.

- `serial_reader.py` can receive and log serial data.
- `dashboard.py` can work with serial and log-driven inputs.
- The packet structure is documented in `serial_protocol.md`.

The remaining work is mainly on the hardware and firmware side.

## Hardware checklist

### Procurement

- [ ] ESP32 board acquired.
- [ ] HC-SR04 ultrasonic sensor acquired.
- [ ] Breadboard acquired.
- [ ] Jumper wires acquired.
- [ ] Stable power arrangement confirmed.

### Bring-up

- [ ] ESP32 powers on reliably.
- [ ] Sensor wiring checked.
- [ ] Echo and trigger pins verified.
- [ ] Safe voltage compatibility confirmed.
- [ ] Basic distance readings observed on serial output.

### Firmware

- [ ] Serial baud rate set to match Python config.
- [ ] Firmware emits exactly 7 fields per line.
- [ ] Distance output validated in centimetres.
- [ ] Speed source decided and implemented.
- [ ] TTC calculation logic verified.
- [ ] Risk classification thresholds aligned with Python config.
- [ ] Confidence field strategy defined.

### Integration test

- [ ] `python src\serial_reader.py --list` sees the board.
- [ ] `python src\serial_reader.py --port COMx` reads packets successfully.
- [ ] `LOGS/live_data.txt` updates correctly.
- [ ] Dashboard reads real data in Live Log mode.
- [ ] Dashboard reads real data in ESP32 Serial mode.

### Validation

- [ ] Distance compared against manual measurement.
- [ ] TTC behaviour checked against expected approach scenarios.
- [ ] Warning threshold observed at the correct timing.
- [ ] Critical threshold observed at the correct timing.
- [ ] Alert latency measured.
- [ ] Fault behaviour tested for noisy or stuck readings.

## Blocking risks

- No hardware has been validated yet.
- The speed-input method is not finalized.
- Firmware output format must stay aligned with `serial_protocol.md`.
- Real sensor noise may require filtering changes.

## Recommended next sequence

1. Finalize the bill of materials.
2. Procure the board and sensor.
3. Implement minimal firmware that only emits valid packets.
4. Confirm Python serial ingestion works before adding extra firmware complexity.
5. Run physical validation tests after the data path is stable.

## When is it actually integrated?

The project should only be called hardware-integrated when:

- Real ESP32 telemetry reaches the Python side.
- The dashboard displays that real telemetry live.
- The sensor values are validated against physical measurements.
- TTC and alert behaviour are verified outside simulation.