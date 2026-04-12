# Hardware Assembly Checklist

Use this checklist for component procurement, wiring, firmware upload, and bring-up.

## Scope

- Target board: ESP32 DevKit-V1 (30-pin)
- Firmware entry sketch: TTC.ino
- Pin mapping source of truth: firmware/pinmap.h

## 1) Procurement Checklist

Required:

- ESP32 DevKit-V1 (30-pin)
- HC-SR04 ultrasonic sensors x2
- MPU6050 IMU module x1
- SSD1306 OLED I2C display x1
- KY-040 rotary encoder x1
- LED indicators: green x2, yellow x2, red x1
- 220 ohm resistors x5
- Active buzzer x1
- Breadboard and jumper wires
- USB cable and stable 5V power source

Optional:

- VL53L1X ToF sensor x1

## 2) Pre-Assembly Verification

- Confirm board variant is 30-pin DevKit-V1.
- Confirm all components are physically intact.
- Confirm power rails and ground rails are continuous.
- Confirm LED polarity and resistor values.

## 3) Wiring Checklist

Apply connections defined in hardware/wiring_guide.md.

- I2C bus: OLED and MPU6050 on D21 (SDA) and D22 (SCL)
- Sonar #1: TRIG D5, ECHO D18
- Sonar #2: TRIG D4, ECHO D16
- Encoder: CLK D19, DT D23
- LEDs: D25, D26, D27, D14, D12
- Buzzer: D32

Power:

- 5V rail for HC-SR04 modules and buzzer if required by module
- 3.3V rail for I2C modules where required
- Common ground for all modules

## 4) Firmware Upload Checklist

- Open TTC.ino in Arduino IDE.
- Select board: ESP32 Dev Module.
- Select correct COM port.
- Compile with Ctrl+R.
- Upload with Ctrl+U.
- Open Serial Monitor at 115200 baud.

Expected output format:

```text
timestamp_ms,distance_cm,speed_kmh,ttc_basic,ttc_ext,risk_class,confidence
```

## 5) Runtime Validation Checklist

- Run dashboard stack with run_dashboard.bat.
- Verify live telemetry updates in dashboard.
- Verify risk-class transitions when distance/speed changes.
- Verify buzzer and LED outputs track risk level.

## 6) Common Failure Checks

- No sensor readings: verify power rails and signal pins.
- OLED blank: verify I2C wiring and address.
- Encoder not changing speed: verify CLK/DT pins.
- Wrong risk behavior: verify threshold sync between src/config.py and firmware/config/config.h.

## Completion Criteria

Assembly is accepted only when:

- Firmware compiles and uploads successfully.
- Serial telemetry is valid and stable.
- Dashboard receives live packets.
- Safety indicators respond correctly to risk-class changes.

## Related Files

- `TTC.ino`
- `firmware/main.ino`
- `firmware/pinmap.h`
- `hardware/wiring_guide.md`
- `docs/simulation-validation-checklist.md`
