# TTC Hardware Assembly Checklist

**Date:** April 11, 2026  
**Status:** Ready for purchase & assembly  
**Est. Assembly Time:** 1–2 hours on breadboard  
**Soldering Required:** No (breadboard only)

---

## 📋 Phase 1: Component Procurement

Print this checklist and take it when ordering from Robu.in, Robocraze.in, or equivalent suppliers.

### Microcontroller (Required)
- [ ] **ESP32 DevKit-V1 (30-pin)** — ⚠️ Must be 30-pin, NOT 38-pin
  - Supplier: Robu.in or Robocraze.in
  - Price: ~₹500–600
  - Verify: "30-pin" in product description

### Distance Sensors (Required)
- [ ] **HC-SR04 Ultrasonic Sensor #1** — Front-facing obstacle detection
  - Qty: 1
  - Price: ~₹100–120
  - Specs: 5V power, range 2cm–400cm
  
- [ ] **HC-SR04 Ultrasonic Sensor #2** — Rear or alternate detection
  - Qty: 1
  - Price: ~₹100–120
  - Same specs as #1

### Accelerometer (Required)
- [ ] **MPU6050 6-axis IMU module** — Measure deceleration
  - Qty: 1
  - Price: ~₹200–250
  - I2C address: 0x68 (default)
  - Specs: ±2g to ±16g selectable

### Display (Required)
- [ ] **SSD1306 OLED I2C Display (128×64)** — Real-time status display
  - Qty: 1
  - Price: ~₹200–250
  - I2C address: 0x3C (verify before buying)
  - Specs: 0.96" diagonal

### Encoder (Required)
- [ ] **KY-040 Rotary Encoder** — Host vehicle speed measurement
  - Qty: 1
  - Price: ~₹50–80
  - Pins: CLK, DT, SW, +, GND
  - (SW button not used; can ignore)

### Alert Outputs (Required)
- [ ] **LED (Green)** — Qty: 2
  - Color: Green (SAFE indicator)
  - Price: ~₹5–10 total
  - Type: Standard 5mm or 3mm

- [ ] **LED (Yellow/Amber)** — Qty: 2
  - Color: Yellow or Amber (WARNING indicator)
  - Price: ~₹5–10 total
  - Type: Standard 5mm or 3mm

- [ ] **LED (Red)** — Qty: 1
  - Color: Red (CRITICAL indicator)
  - Price: ~₹2–5
  - Type: Standard 5mm or 3mm

- [ ] **Current-limiting Resistors (220Ω)** — Qty: 5
  - Value: 220Ω, 1/4W
  - Price: ~₹5–10 total
  - Purpose: Limit LED current to ~15mA

- [ ] **Active Buzzer** — Qty: 1
  - Voltage: 5V
  - Price: ~₹20–40
  - ⚠️ Must be **ACTIVE** (self-oscillating), NOT passive
  - Look for: "active buzzer" or "piezo buzzer with oscillator"

### Optional: ToF LIDAR (Not Required)
- [ ] **VL53L1X Time-of-Flight Sensor** — Better distance accuracy at range
  - Qty: 1 (optional)
  - Price: ~₹800–1000
  - I2C address: 0x29
  - Only buy if you set `USE_VL53L1X=1` in firmware/config/config.h
  - Can omit: Two HC-SR04s already provide good coverage

### Breadboard & Wiring (Required)
- [ ] **Breadboard (830-point minimum)**
  - Qty: 1–2 (1 is minimum, 2 is comfortable)
  - Price: ~₹100–200 for 2
  - Layout: Should have power rails on both sides

- [ ] **Jumper Wires** — Qty: 50+ pack
  - Colors: Mixed (red, black, blue, green)
  - Price: ~₹50–100
  - Length: 15–20cm assorted

- [ ] **USB-A to Micro-USB Cable** — Qty: 1
  - For: ESP32 programming and power
  - Length: 1–2 meters
  - Price: ~₹20–50

### Power Supply
- [ ] **Micro-USB Power Adapter (5V, 2A minimum)**
  - For: Breadboard power rail
  - Price: ~₹100–200
  - Make sure: Powers breadboard 5V rail for HC-SR04, encoder, buzzer

### Optional: Capacitors (Recommended)
- [ ] **Electrolytic Capacitors (100µF)**  — Qty: 2
  - Purpose: Reduce power spikes to HC-SR04 sensors
  - Price: ~₹5–10
  - Voltage rating: 16V minimum
  - (Can omit if stable power supply)

---

## 💰 Total Budget Estimate

| Category | Qty | Unit Price | Total |
|----------|-----|------------|-------|
| ESP32 DevKit-V1 | 1 | ₹500 | ₹500 |
| HC-SR04 Ultrasonic | 2 | ₹110 | ₹220 |
| MPU6050 IMU | 1 | ₹225 | ₹225 |
| SSD1306 OLED | 1 | ₹225 | ₹225 |
| KY-040 Encoder | 1 | ₹65 | ₹65 |
| LEDs (5 total) | 5 | ₹8 | ₹40 |
| Resistors (220Ω, 5×) | 5 | ₹2 | ₹10 |
| Active Buzzer | 1 | ₹30 | ₹30 |
| Breadboard (2×) | 2 | ₹150 | ₹300 |
| Jumper Wires | 1 | ₹75 | ₹75 |
| USB Cable | 1 | ₹35 | ₹35 |
| Power Adapter | 1 | ₹150 | ₹150 |
| **SUBTOTAL** | — | — | **₹1,875** |
| VL53L1X LIDAR (optional) | 1 | ₹900 | ₹900 |
| **TOTAL (with LIDAR)** | — | — | **₹2,775** |

---

## 🔧 Phase 2: Hardware Assembly (Before Power-On)

### Pre-Assembly Checks
- [ ] **Verify all components received** — Check against checklist above
- [ ] **Test breadboard** — Insert wire in each row, confirm contact
- [ ] **Check USB cable** — Plug into ESP32, verify it powers up (should light indicator LED)
- [ ] **Verify LED polarity** — Longer leg (anode) goes to resistor, shorter leg (cathode) to GND

### Wiring Reference
**Use `firmware/pinmap.h` as your source of truth!**

Quick pin map (from `docs/hardware_wiring_guide.md`):
```
HC-SR04 #1:     TRIG→D5,   ECHO→D18
HC-SR04 #2:     TRIG→D4,   ECHO→D16
Encoder:        CLK→D19,   DT→D23
OLED (I2C):     SDA→D21,   SCL→D22
MPU6050 (I2C):  SDA→D21,   SCL→D22 (same pins!)
LEDs:           D25, D26 (green), D27, D14 (yellow), D12 (red)
Buzzer:         D32
```

### Assembly Steps
- [ ] **Step 1:** Insert breadboard power rails
  - Red: 5V power
  - Black: GND
  - Blue/Green: Secondary rail (can use for 3.3V)

- [ ] **Step 2:** Mount ESP32 on breadboard
  - Pins facing outward
  - Leave space above for sensor connections

- [ ] **Step 3:** Wire I2C devices (OLED + MPU6050)
  - Both share SDA (D21) and SCL (D22)
  - Different addresses: OLED=0x3C, MPU6050=0x68
  - Connect 3.3V power and GND

- [ ] **Step 4:** Wire HC-SR04 sensors
  - Power: VIN (5V, not 3.3V!)
  - GND: Common ground
  - TRIG & ECHO to specified pins (see pinmap)

- [ ] **Step 5:** Wire encoder
  - CLK to D19 (with internal pull-up in firmware)
  - DT to D23
  - Power from VIN (5V)
  - GND to common

- [ ] **Step 6:** Wire LEDs with resistors
  - 220Ω resistor in series with each LED anode
  - Cathode to GND
  - Anode+resistor end to specified GPIO

- [ ] **Step 7:** Wire buzzer
  - Positive to D32
  - Negative (GND) to common ground

- [ ] **Final checks before power:**
  - [ ] No jumpers touching each other
  - [ ] All GND connections are solid
  - [ ] No loose wires in breadboard
  - [ ] ESP32 powers on when connected (LED blinks)
  - [ ] Measure with multimeter: power rails are 5V and 3.3V

---

## 💻 Phase 3: Firmware Upload & Testing

### Prerequisites
- Arduino IDE installed
- ESP32 board package installed
- Adafruit libraries installed (see README.md)
- Firmware fixes applied (✅ already done)

### Steps
- [ ] **Connect ESP32 via USB** — Should appear as COM port
- [ ] **Open `TTC.ino`** in Arduino IDE
- [ ] **Select Board:** Tools → Board → ESP32 Dev Module
- [ ] **Select Port:** Tools → Port → COMx (your ESP32)
- [ ] **Compile:** Ctrl+R → Should complete with 0 errors
- [ ] **Upload:** Ctrl+U → LED on ESP32 should flash
- [ ] **Open Serial Monitor:** Tools → Serial Monitor (115200 baud)
  - Should see CSV lines like: `1000,245.30,0.00,99.00,99.00,0,0.90`

### Testing
- [ ] **Power on breadboard** — All components should power up
- [ ] **Green LEDs light** — OLED should display (or confirm in Serial Monitor)
- [ ] **Sensor readings appear** — Serial Monitor shows distance, speed values
- [ ] **Block sonar #1 with hand** — Should see distance decrease
- [ ] **Rotate encoder** — Should see speed values change

---

## 🖥️ Phase 4: Python Integration

### Start Python Dashboard
```bash
cd C:\Users\niroo\Downloads\TTC
python src/dashboard.py
```

### Connect Hardware Serial
```bash
python src/serial_reader.py --port COM3
# (Replace COM3 with your actual port)
```

### Verify Data Flow
- [ ] Dashboard displays live metrics
- [ ] Distance, speed, TTC values update in real-time
- [ ] LEDs on hardware blink in sync with dashboard
- [ ] Alerts trigger when TTC drops below thresholds

---

## ⚠️ Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| HC-SR04 shows 0 distance | Power is 3.3V instead of 5V | Check VIN (5V rail) is connected, not 3.3V |
| OLED is blank | I2C address wrong or power issue | Verify address 0x3C; check 3.3V power |
| Encoder not counting | Pull-ups missing | Verify firmware has `pinMode(PIN, INPUT_PULLUP)` |
| Buzzer won't turn off | GPIO stuck HIGH | Test with `digitalWrite(D32, LOW)` command |
| ESP32 won't upload | COM port not selected | Check Tools → Port → select COM port |

---

## ✅ Final Checklist (Before Deployment)

- [ ] All 13 components purchased and received
- [ ] Breadboard assembly complete per pinmap.h
- [ ] No jumper wires crossing unnecessarily
- [ ] All GND connections verified with multimeter
- [ ] Power rails measure correct voltage (5V, 3.3V)
- [ ] USB cable connects ESP32 to computer
- [ ] Arduino IDE successfully compiles firmware (0 errors)
- [ ] Arduino IDE successfully uploads to ESP32
- [ ] Serial Monitor shows CSV output (115200 baud)
- [ ] Dashboard starts without import errors
- [ ] Dashboard receives live telemetry from hardware

**If all checks pass: ✅ System is deployed and operational!**

---

**Prepared by:** TTC Project  
**Date:** April 11, 2026  
**Version:** 1.0 (Hardware-Ready)
