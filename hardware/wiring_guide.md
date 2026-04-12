# Hardware Wiring Guide

This guide defines the supported wiring layout for TTC hardware bring-up.

## Scope

- Board: ESP32 DevKit-V1 (30-pin)
- Firmware pin source: firmware/pinmap.h
- I2C devices: SSD1306 OLED and MPU6050 on shared bus

## Pin Map

| Component | Signal | ESP32 Pin |
| --- | --- | --- |
| HC-SR04 #1 | TRIG | D5 |
| HC-SR04 #1 | ECHO | D18 |
| HC-SR04 #2 | TRIG | D4 |
| HC-SR04 #2 | ECHO | D16 |
| Encoder | CLK | D19 |
| Encoder | DT | D23 |
| OLED | SDA | D21 |
| OLED | SCL | D22 |
| MPU6050 | SDA | D21 |
| MPU6050 | SCL | D22 |
| LED Safe #1 | OUT | D25 |
| LED Safe #2 | OUT | D26 |
| LED Warning #1 | OUT | D27 |
| LED Warning #2 | OUT | D14 |
| LED Critical | OUT | D12 |
| Buzzer | OUT | D32 |

## Power Mapping

| Rail | Usage |
| --- | --- |
| 3.3V | OLED, MPU6050 |
| 5V | HC-SR04 modules, encoder module power where required |
| GND | Common ground for all modules |

## Wiring Rules

- Keep all grounds common.
- Add 220 ohm resistor in series for each LED output.
- Use active buzzer module for direct digital drive.
- Keep I2C bus wiring short and clean.
- Do not deviate from firmware/pinmap.h unless firmware is updated in the same change.

## Optional Sensors

VL53L1X integration is optional and must be explicitly enabled in firmware/config/config.h.

## Pre-Power Checklist

- Verify no short between power rails.
- Verify each signal pin matches the pin map.
- Verify all LED resistors are installed.
- Verify I2C devices share D21/D22 correctly.

## Bring-Up Checks

- Firmware uploads without pin initialization errors.
- Serial telemetry emits valid 7-field packets.
- Distance and speed signals update under controlled input.
- LED and buzzer behavior tracks risk class.

## Related Files

- `firmware/pinmap.h`
- `firmware/config/config.h`
- `hardware/assembly_checklist.md`
