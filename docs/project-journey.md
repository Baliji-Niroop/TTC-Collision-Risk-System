# Project Journey: Engineering the TTC Collision Risk System

**Author:** Baliji Niroop  
**Discipline:** B.Tech in Automobile Engineering  
**Institution:** VNR Vignana Jyothi Institute of Engineering and Technology (VNR VJIET), Hyderabad  

---

## 1. Problem Statement & Motivation
Rear-end collisions are among the most frequent types of road accidents worldwide, contributing to thousands of fatal injuries and substantial property damage every year. Many entry-level vehicles and educational prototypes lack active collision warning systems due to the cost and complexity of high-end radar/vision ADAS suites.

As an automobile engineering student, the goal of this capstone project was to design, build, and validate an **accessible, deterministic Time-To-Collision (TTC) risk prediction system** integrating physical sensors, embedded edge microcontrollers (ESP32), and host-level Python telemetry analytics.

---

## 2. Theoretical Foundation & Kinematic Modeling
The project began by examining longitudinal vehicle dynamics and standard active safety metrics:
- **Constant Velocity Approximation:** $TTC = d / v_{\text{closing}}$. Simple and fast, but fails when vehicles are actively braking.
- **Deceleration Kinematics:** Formulated extended TTC incorporating vehicle braking capability $a$ ($\approx 5.0\,\text{m/s}^2$):
  $$d(t) = d - v_{\text{closing}} t + \frac{1}{2} a t^2$$
  Solving for roots gave the exact stopping envelope and eliminated false alarms when braking is already adequate.
- **Surface Friction Multipliers:** Incorporated tyre-road friction coefficients ($\mu$) to dynamically extend critical headway on wet, gravel, or icy roads.

---

## 3. Hardware Prototyping & Sensor Architecture
- Selected the **ESP32 DevKit-V1** for its dual-core architecture and hardware interrupt support.
- Configured distance sensing using the HC-SR04 ultrasonic sensor and VL53L1X Time-of-Flight LIDAR.
- Implemented speed estimation using a KY-040 rotary optical encoder on the vehicle wheel.
- Added I2C SSD1306 OLED display for driver feedback, complemented by 5 status LEDs and an active buzzer.
- Developed a comprehensive simulation model in **Wokwi** (`diagram.json`) allowing repeatable hardware-in-the-loop testing without bench risk.

---

## 4. Telemetry Contract & Embedded Firmware
To ensure bulletproof communication between the microcontroller and analytical software, the serial protocol was strictly frozen into a **canonical 7-field CSV contract**:
```text
timestamp_ms, distance_cm, speed_kmh, ttc_basic, ttc_ext, risk_class, confidence
```
- Implemented on ESP32 running at $10\,\text{Hz}$ ($100\,\text{ms}$ loop).
- Created a rolling 3-point circular buffer to compute smooth relative closing speeds while eliminating ultrasonic noise spikes.

---

## 5. Machine Learning & Edge Deployment
While physics provides hard safety guarantees, machine learning was explored to assist classification in complex, noisy conditions:
- **Exploration:** Evaluated Logistic Regression (accuracy $\approx 70\%$) and Support Vector Machines, but found them lacking in either non-linear capability or deployment ease.
- **Dual-Model Architecture:**
  1. *Host / Cloud Model:* Random Forest Classifier ($50$ trees) achieving $96.5\%$ cross-validation accuracy.
  2. *Embedded Edge Model:* Decision Tree (depth $\le 4$) achieving $99.5\%$ classification accuracy.
- **C++ Code Generation:** Built an automated script (`tree2C` in `train_model.py`) that exports the trained Decision Tree into a zero-dependency C++ header (`ml_classifier.h`) executing in $<1\,\text{ms}$ on ESP32.
- **Safety Arbitration Rule:** Implemented a hard constraint in firmware: *ML inference is strictly prohibited from overriding or downgrading a physical kinematic CRITICAL state*.

---

## 6. Host Software, Validation Suite, & Dashboard
- Developed an interactive **Streamlit live dashboard** featuring real-time speedometer gauges, TTC trajectory charts, and alert logs.
- Engineered automated validation gates:
  - `protocol_contract_test.py`: Verifies syntax, token counts, and alias rejection.
  - `evaluate_synthetic.py`: Tests 610 multi-scenario kinematic benchmark cases, confirming **$100\%$ critical recall** and **$0\%$ false alarm rate**.
  - `pin_validator.py`: Cross-checks GPIO definitions across firmware, diagrams, and bridges.

---

## 7. Lessons Learned & Next Steps
- **Hardware-Software Timing:** Sensor acquisition jitter can severely distort velocity derivatives. Implementing a circular time-stamped buffer was critical for smooth closing speed estimation.
- **Safety Over ML Hype:** In automotive active safety, explainable deterministic physics must always act as the fail-safe supervisor over probabilistic ML models.
- **Future Work:**
  - CAN bus integration (ISO 11898) for production automotive vehicle speed ingestion.
  - Camera sensor fusion using a low-power edge vision module (ESP32-CAM or OpenCV).
  - Physical closed-course track testing on a scaled electric kart platform.
