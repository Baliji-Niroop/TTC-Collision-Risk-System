# TTC Hardware Wiring Guide

**Date:** April 11, 2026  
**Target Platform:** ESP32 DevKit-V1 (30-pin variant)  
**Simulation:** Wokwi  
**Source of Truth:** `firmware/pinmap.h`

---

## Before You Start

- **ESP32 variant matters.** You need the **30-pin DevKit-V1**, NOT the 38-pin variant. Pin assignments differ.
- **All pin numbers in this guide come from `firmware/pinmap.h`** — if you change them there, update this guide to match.
- **I2C bus is shared** — both the OLED display and MPU6050 accelerometer use the same SDA/SCL pins (D21/D22) but at different I2C addresses (0x3C for OLED, 0x68 for MPU6050).
- **Resistors required** — Every LED needs a 220Ω current-limiting resistor in series.
- **Active buzzer expected** — The code assumes an active (self-oscillating) buzzer, not passive.

---

## Quick Pin Map

| Component | ESP32 Pin | Notes |
|-----------|-----------|-------|
| **HC-SR04 #1 TRIG** | D5 | Trigger pulse (output) |
| **HC-SR04 #1 ECHO** | D18 | Echo time measurement (input) |
| **HC-SR04 #2 TRIG** | D4 | Secondary sonar trigger |
| **HC-SR04 #2 ECHO** | D16 | Secondary sonar echo |
| **Encoder CLK** | D19 | Rotary encoder clock (interrupt) |
| **Encoder DT** | D23 | Rotary encoder direction |
| **OLED SDA** | D21 | I2C data (shared bus) |
| **OLED SCL** | D22 | I2C clock (shared bus) |
| **MPU6050 SDA** | D21 | I2C data (same bus, different address) |
| **MPU6050 SCL** | D22 | I2C clock (same bus, different address) |
| **LED Green #1** | D25 | 220Ω resistor required |
| **LED Green #2** | D26 | 220Ω resistor required |
| **LED Yellow #1** | D27 | 220Ω resistor required |
| **LED Yellow #2** | D14 | 220Ω resistor required |
| **LED Red** | D12 | 220Ω resistor required |
| **Buzzer +** | D32 | Active buzzer, GND to GND |

---

## Power Rails

| Connection | ESP32 Pin | Notes |
|------------|-----------|-------|
| **3.3V rail** | 3V3 | Powers: OLED, MPU6050, HC-SR04 (power pins) |
| **5V rail** | VIN | Powers: Encoders, HC-SR04 (power pins) |
| **Ground** | GND | All GND connections tied together |

---

## Detailed Wiring Instructions

### 1. Ultrasonic Sensors (HC-SR04 x2)

#### Sensor #1 (Front-facing distance)
```
HC-SR04 Pin → ESP32 Pin
───────────────────────
VCC      → VIN (5V)
GND      → GND
TRIG     → D5
ECHO     → D18
```

#### Sensor #2 (Rear or alternate detection)
```
HC-SR04 Pin → ESP32 Pin
───────────────────────
VCC      → VIN (5V)
GND      → GND
TRIG     → D4
ECHO     → D16
```

**Notes:**
- HC-SR04 requires 5V power; 3.3V will not work reliably
- ECHO output is 5V TTL; ESP32 GPIO is 3.3V tolerant, so no level shifter needed (Arduino sketches don't require it)
- Recommended: Add 100µF capacitor across VCC–GND for each sensor to reduce power spikes

---

### 2. I2C Devices (Shared Bus)

Both the OLED and MPU6050 use the same two pins (D21 SDA, D22 SCL) but listen at different addresses.

```
OLED (SSD1306)          MPU6050 (Accelerometer)
──────────────────────  ─────────────────────────
VCC → 3V3               VCC → 3V3
GND → GND               GND → GND
SDA → D21               SDA → D21  (same pin!)
SCL → D22               SCL → D22  (same pin!)
(addr: 0x3C)            (addr: 0x68)
```

**Optional pull-up resistors:**
- If using long I2C wires (>1m) or multiple devices, add 4.7kΩ pull-ups from SDA→3V3 and SCL→3V3
- ESP32 has internal pull-ups, so often not needed for short breadboard distances
- Test first without; add if you see I2C errors in Serial Monitor

**I2C Addresses (do not change):**
- OLED: `0x3C` (hardcoded in firmware/config/config.h)
- MPU6050: `0x68` (hardcoded in firmware/config/config.h)
- VL53L1X LIDAR (if installed): `0x29` (optional, set `USE_VL53L1X = 1` in config.h)

---

### 3. Wheel Encoder (KY-040 Rotary Encoder)

```
KY-040 Pin → ESP32 Pin
──────────────────────
CLK        → D19 (with pull-up)
DT         → D23 (with pull-up)
SW         → Not connected (button not used)
+          → VIN (5V)
GND        → GND
```

**Pull-up resistors:**
- Use either internal (enabled via `pinMode(PIN, INPUT_PULLUP)` — already in firmware) or external 10kΩ pull-ups from CLK/DT to VIN
- Internal pull-ups are sufficient for breadboard distances

**Direction detection:**
- Firmware reads CLK as the interrupt pin, DT as the direction reference
- If counted pulses are inverted, swap CLK/DT connections

---

### 4. LED Alert Bar (Visual Indicators)

Each LED requires a **220Ω resistor in series** to limit current to ~15mA per LED (safe for ESP32 GPIO).

```
LED Anode (longer leg) → 220Ω Resistor → ESP32 Pin
LED Cathode (shorter)  → GND
```

| LED Color | ESP32 Pin | Signal State |
|-----------|-----------|--------------|
| Green #1 | D25 | HIGH = SAFE |
| Green #2 | D26 | HIGH = SAFE |
| Yellow #1 | D27 | HIGH = WARNING |
| Yellow #2 | D14 | HIGH = WARNING |
| Red | D12 | HIGH = CRITICAL |

**Breadboard layout tip:**
- Place all 5 resistors in one column
- Connect their other ends (without resistor) to GND rail via a manifold

---

### 5. Buzzer (Active)

```
Buzzer + → D32
Buzzer - → GND
```

**Important:** This must be an **active buzzer** (self-oscillating), not a passive piezo speaker. Active buzzers have built-in oscillators and only need HIGH/LOW GPIO, while passive piezo requires PWM frequency.

**Current limiting:**
- Active buzzers typically draw 20–40mA; ESP32 GPIO can supply ~40mA per pin
- If buzzer is dim, check VIN power supply has sufficient current capacity

---

## Breadboard Layout Diagram

```
                    ┌──────────────────────────────────┐
                    │      ESP32 DevKit-V1             │
                    │  (30-pin, front-facing USB)      │
                    │                                  │
              ┌─────┤D5 D18 D4 D16 D19 D23 D21 D22     ├─────┐
              │     │                                  │     │
              │     │D25 D26 D27 D14 D12 D32           │     │
              │     │                                  │     │
              │     │VIN GND 3V3 ... (other pins)      │     │
              │     └──────────────────────────────────┘     │
              │                                              │
        ┌─────┴─────┐
        │ Ultrasonic │  ┌────────────────────────────────┐
        │   Sensors  │  │  I2C Devices (Shared Bus)      │
        │            │  │  ┌──────────────┬───────────┐  │
   TRIG─D5      ┌────┤  │  │ OLED(0x3C)   │MPU(0x68)  │  │
   ECHO─D18     │    │  │  │ SDA─D21─SDA  └─SDA       │  │
  TRIG2─D4  ┌───┤    │  │  │ SCL─D22─SCL  └─SCL      │  │
  ECHO2─D16 │   │    │  │  └──────────────┬───────────┘  │
            │   │    │  └────────────────────────────────┘
            │   │    │
        ┌───┴───┴────┴──────────────────────┐
        │  GND        VIN (5V)        3V3   │
        │───────────────────────────────────│
        │ Power Rail                        │
        └───────────────────────────────────┘

        ┌─────────────────────────────────────────┐
        │ Encoder (D19, D23), LEDs (D25-D27,      │
        │ D14, D12), Buzzer (D32)                 │
        │ (Connect to power rails above)          │
        └─────────────────────────────────────────┘
```

---

## Validation Checklist

Before powering on:

- [ ] **Pin numbers match `firmware/pinmap.h`** — do a quick visual scan
- [ ] **All LEDs have 220Ω resistors in series** — measure with multimeter if unsure
- [ ] **I2C devices (OLED + MPU) share D21/D22** but are at different addresses
- [ ] **HC-SR04 power is VIN (5V), not 3V3** — wrong voltage will cause no readings
- [ ] **Buzzer is active (has built-in oscillator), not passive** — ask seller if unsure
- [ ] **No jumpers cross each other unnecessarily** — reduces shorts
- [ ] **GND connections are solid** — use multiple GND points across the breadboard
- [ ] **Encoder has pull-ups** — either internal (enabled in firmware) or external 10kΩ
- [ ] **No floating pins** — if a pin is not used, leave it unconnected

---

## Troubleshooting

### OLED does not display anything
- Check I2C address is 0x3C (some clones use 0x3D)
- Verify SDA/SCL are on D21/D22
- Check pull-ups: if internal aren't enough, add 4.7kΩ external

### HC-SR04 shows no distance (always 0 or max range)
- Verify power is VIN (5V), not 3V3
- Check TRIG and ECHO pins match pinmap.h
- Confirm ECHO wire is connected (if it reads max range, ECHO is floating)

### Encoder not counting pulses
- Verify CLK and DT are on D19 and D23
- Check pull-ups are enabled (should be in firmware)
- Try swapping CLK/DT if pulses are inverted

### MPU6050 not responding on I2C
- Confirm address is 0x68 (some boards default to 0x69 with ADO pin tied high)
- Verify SDA/SCL on D21/D22, same as OLED
- Check pull-ups

### Buzzer won't turn off
- Verify GPIO D32 can go LOW (digitalWrite(D32, LOW) in code)
- Check power supply isn't stuck HIGH
- Verify it's an active buzzer, not passive

---

## Optional: VL53L1X LIDAR (ToF Distance Sensor)

If you decide to add the optional LIDAR distance sensor:

```
VL53L1X (I2C) → ESP32
──────────────────────
VCC       → 3V3
GND       → GND
SDA       → D21 (shared I2C bus)
SCL       → D22 (shared I2C bus)
```

**To enable in firmware:**
1. Set `#define USE_VL53L1X 1` in `firmware/config/config.h`
2. Recompile and upload
3. Check I2C address: VL53L1X defaults to 0x29

**Why optional?**
- Two HC-SR04 units with Kalman fusion already provide good distance measurement
- LIDAR adds cost (~₹800–1000) but improves accuracy at longer ranges (>1m)
- Firmware gracefully falls back to sonar if LIDAR is missing

---

## References

- **ESP32 Pinout:** https://randomnerdtutorials.com/esp32-pinout-reference-gpios/
- **HC-SR04 Datasheet:** HC-SR04 ultrasonic sensor spec
- **MPU6050 Datasheet:** InvenSense 6-axis MEMS IMU
- **KY-040 Encoder:** Standard rotary encoder pinout
- **Firmware Config:** `firmware/pinmap.h` (single source of truth)

---

**Last Updated:** April 11, 2026  
**Maintainer:** TTC Project  
**Status:** Production-Ready for Breadboard Assembly
