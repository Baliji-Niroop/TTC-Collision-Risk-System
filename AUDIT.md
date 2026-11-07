# AUDIT REPORT: TTC Collision Risk System

**Date:** 2026-11-07  
**Branch:** docs/10-out-of-10-cleanup  
**Auditor:** Senior Software Engineer & Technical Writer (AI Pair Programmer)

---

## 1. What the Project Does (Plain Sentences)
1. The TTC Collision Risk System is an Advanced Driver Assistance System (ADAS) project that monitors relative distance and closing speed to forward obstacles in real time.
2. It computes Time-to-Collision (TTC) using both constant-velocity and deceleration-aware kinematic models, and classifies road collision hazard into Safe, Warning, or Critical states using deterministic thresholds and an edge-deployable machine learning model.
3. The system runs on embedded microcontrollers (ESP32 / Wokwi simulation) connected to physical or simulated distance sensors and wheel speed encoders, streaming a standardized 7-field telemetry contract to a Python live dashboard and validation analytics suite.

---

## 2. Full File / Folder Tree with One-Line Purpose

```text
TTC-Collision-Risk-System/
├── .editorconfig                          # Editor formatting settings (indentation, charset)
├── .flake8                                # Flake8 linter configuration and max-line-length rules
├── .gitignore                             # Git ignore rules for virtualenvs, caches, logs, models
├── .github/
│   ├── ci.yml                             # GitHub Actions CI workflow (linting, tests, validation)
│   └── copilot-instructions.md            # Guidelines for coding assistants working on the repository
├── .vscode/                               # VS Code configuration directory (tasks, settings)
├── bridge/
│   └── wokwi_serial_bridge.py             # Bridges Wokwi web simulation websocket/stdin to COM ports and live logs
├── config/
│   └── __init__.py                        # Top-level config package marker
├── dataset/
│   └── synthetic_ttc_validation.csv       # 610-sample kinematic driving scenarios dataset with ground truth
├── diagram.json                           # Wokwi simulation wiring diagram (ESP32, sensors, LEDs, buzzer)
├── docs/
│   ├── naming-and-structure-policy.md     # Codebase style conventions and directory structure rules
│   ├── PROJECT_MAP.md                     # Beginner roadmap and module-by-module tour
│   ├── README.md                          # Documentation index linking hardware and protocol specs
│   ├── serial_protocol.md                 # Specifications for the 7-field CSV serial telemetry contract
│   ├── simulation-validation-checklist.md # Manual & automated regression checklist for simulator/hardware
│   └── wokwi_bridge_smoke_test.md         # Guide for running smoke tests on the Wokwi serial bridge
├── firmware/
│   ├── alert_controller.h                 # Alerts controller abstraction for LEDs and audio alarms
│   ├── circular_buffer.h                  # Fixed-size circular buffer for distance history
│   ├── data_logger.h                      # Embedded logging utilities
│   ├── main.ino                           # Primary Arduino/ESP32 firmware runtime implementation
│   ├── ml_classifier.h                    # Root copy of exported ML classifier decision tree
│   ├── pinmap.h                           # Authoritative GPIO pin assignments matching diagram.json
│   ├── sensor_drivers.h                   # Low-level HC-SR04, VL53L1X, and KY-040 sensor drivers
│   ├── sensor_fusion.h                    # Weighted complementary filter for ultrasonic and lidar distance
│   ├── system_state.h                     # Data structures holding vehicle state, distance, and risk
│   ├── ttc_calculator.h                   # Kinematic calculation header for TTC
│   ├── alerts/
│   │   ├── oled_display.h                 # SSD1306 I2C OLED display driver and UI screens
│   │   └── risk_classifier.h              # Deterministic risk classification with road condition multipliers
│   ├── config/
│   │   ├── arduino_compat.h               # Cross-platform compatibility shims for Arduino primitives
│   │   ├── config.h                       # Firmware operational parameters, thresholds, and legacy note
│   │   └── serial_protocol.h              # C++ implementation of the 7-field serial telemetry packet emitter
│   ├── ml/
│   │   └── ttc_engine.h                   # Embedded velocity estimation and TTC basic/extended formulas
│   ├── ml_classifier/
│   │   └── ml_classifier.h                # Auto-generated C++ Decision Tree if-else code for edge inference
│   └── sensors/
│       └── sensors.h                      # Sensor interface definitions and encoder tracking
├── hardware/
│   ├── assembly_checklist.md              # Physical assembly and bench check instructions
│   ├── README.md                          # Hardware components inventory and bill of materials
│   └── wiring_guide.md                    # Pin-by-pin wiring instructions matching ESP32 pinmap
├── LICENSE                                # MIT open-source license
├── LOGS/                                  # Runtime log storage (live_data.txt, session CSVs)
├── ml/
│   ├── __init__.py                        # ML module root package marker
│   ├── inference/
│   │   └── __init__.py                    # Model loading and inference helper with physics fallback
│   └── training/
│       └── train_model.py                 # Trains Random Forest (server) & Decision Tree + exports C++ header
├── MODELS/
│   └── ml_model.pkl                       # Trained scikit-learn Random Forest model artifact
├── README.md                              # Main repository overview, quick start, and system architecture
├── requirements-dev.txt                   # Developer and CI dependencies (pytest, black, flake8, mypy)
├── requirements.txt                       # Core Python runtime dependencies (pyserial, streamlit, plotly, etc.)
├── run_dashboard.bat                      # Windows launcher starting simulator, Streamlit dashboard, and browser
├── run_wokwi_bridge.bat                   # Windows launcher starting Wokwi serial bridge
├── src/
│   ├── alerts.py                          # Alert manager with throttling to prevent alert spam
│   ├── analytics.py                       # Statistical analysis, risk distribution, and driving metrics
│   ├── config.py                          # Central Python configuration, file paths, and risk thresholds
│   ├── dashboard.py                       # Interactive Streamlit live dashboard with metrics and charts
│   ├── logger.py                          # Unified logging setup across all Python modules
│   ├── replay_runner.py                   # Replays recorded session CSVs through the analytics pipeline
│   ├── safety_features.py                 # Risk hysteresis, sensor fault detection, and ML confidence fusion
│   ├── serial_reader.py                   # Ingests live telemetry from ESP32 serial COM ports
│   ├── serial_simulator.py                # Standalone simulator generating synthetic kinematic telemetry
│   ├── synthetic_validation_dataset.py    # Generator for multi-scenario synthetic validation datasets
│   ├── telemetry_schema.py                # Telemetry 7-field packet serialization and parsing
│   ├── utils.py                           # File system verification and log summarization utilities
│   └── validators.py                      # Data validation and anomaly detection for incoming packets
├── tests/
│   ├── conftest.py                        # Pytest fixtures and environment setup
│   ├── test_analytics.py                  # Unit tests for risk threshold classification
│   ├── test_config.py                     # Unit tests for configuration constants and path sanity
│   └── test_validators.py                 # Unit tests for packet validation and anomaly detection
├── TTC.ino                                # Arduino IDE root entry point that includes firmware/main.ino
├── validation/
│   ├── capture_demo_evidence.py           # Runs smoke tests and collects artifacts for CI/documentation
│   ├── compare_wokwi_baseline.py          # Compares recorded Wokwi sessions against expected baselines
│   ├── evaluate_synthetic.py              # Evaluates model performance on synthetic validation data
│   ├── pin_validator.py                   # Verifies consistency between pinmap.h, diagram.json, and bridge
│   ├── protocol_contract_test.py          # Validates strict compliance with the 7-field telemetry contract
│   └── outputs/                           # Validation evaluation plots, confusion matrices, and metrics
└── wokwi.toml                             # Wokwi simulator project configuration file
```

---

## 3. Tech Stack
- **Firmware / Hardware:**
  - Microcontroller: ESP32 DevKit-V1 (Dual-Core Tensilica Xtensa 32-bit LX6)
  - Language: C / C++ (Arduino Framework, C++11 standard)
  - Sensors: HC-SR04 Ultrasonic Sensor, VL53L1X Time-of-Flight LIDAR, KY-040 Rotary Wheel Encoder, MPU6050 6-DOF IMU
  - Actuators / Displays: SSD1306 128x64 I2C OLED Display, 5x Status LEDs (2 Green, 2 Yellow, 1 Red), Active Buzzer
  - Simulation Environment: Wokwi Simulator (`wokwi.toml`, `diagram.json`)
- **Software / Analytics:**
  - Language: Python (supports 3.10 through 3.15)
  - GUI / Dashboard: Streamlit (interactive web interface), Plotly (real-time charts)
  - Data Science / ML: NumPy, Pandas, Scikit-Learn (Random Forest & Decision Tree), Joblib, Matplotlib
  - I/O & Bridging: PySerial, Websocket-client
  - Quality & Testing: Pytest, Flake8

---

## 4. Inputs and Outputs
- **Inputs:**
  - Front obstacle distance $d$ (cm) via ultrasonic / ToF LIDAR sensor fusion.
  - Host vehicle speed $v$ (km/h) via wheel encoder pulse tracking ($v = (\Delta\text{pulses} \cdot \text{circ}) / (\text{PPR} \cdot \Delta t)$).
  - Closing speed $v_{\text{closing}}$ (km/h) via difference in distance buffer over $\Delta t$.
  - Optional road condition flags (0=Dry, 1=Wet, 2=Gravel, 3=Ice).
  - Deceleration capability $a$ ($\approx 5.0\,\text{m/s}^2$ default).
- **Telemetry Contract (7 Fields, CSV over Serial / WebSocket):**
  ```text
  timestamp_ms, distance_cm, speed_kmh, ttc_basic, ttc_ext, risk_class, confidence
  ```
- **Outputs:**
  - Real-time Risk Level: `0 = SAFE` (Green LEDs), `1 = WARNING` (Yellow LEDs + intermittent beep), `2 = CRITICAL` (Red LED + continuous siren).
  - SSD1306 OLED Screen: Live distance, speed, TTC, and graphical risk bar.
  - Streamlit Web Dashboard: Live gauges, TTC trend line, risk classification distribution, alert logs.
  - Persistent Session Logs: CSV recording in `LOGS/session_YYYYMMDD_HHMMSS.csv` for post-drive analytics.

---

## 5. Core Algorithm in Plain Steps

1. **Distance & Speed Acquisition:**
   - Raw distance samples from ultrasonic sensor (and optional LIDAR) are filtered through a complementary / Kalman filter.
   - Host vehicle speed is measured via wheel encoder interrupts.
   - Relative closing speed $v_{\text{closing}}$ ($\text{m/s}$) is computed using a 3-point rolling circular buffer:
     $$v_{\text{closing}} = \frac{d_{t - \Delta t} - d_t}{\Delta t}$$
2. **Time-To-Collision (TTC) Calculation:**
   - **Basic TTC (Constant-Velocity Model):**
     $$\text{TTC}_{\text{basic}} = \frac{d}{v_{\text{closing}}} \quad (\text{if } v_{\text{closing}} > 0.1\,\text{m/s}, \text{ else } 99.0\,\text{s})$$
   - **Extended TTC (Constant-Deceleration Model):**
     Accounting for maximum braking deceleration $a$ ($\text{m/s}^2$):
     $$\text{TTC}_{\text{ext}} = \frac{-v_{\text{closing}} + \sqrt{v_{\text{closing}}^2 + 2 a d}}{a} \quad (\text{or } 99.0\,\text{s if } v_{\text{closing}}^2 + 2ad < 0)$$
3. **Risk Classification:**
   - Evaluated against standard ADAS safety time margins:
     - **CRITICAL (Level 2):** $\text{TTC} \le 1.5\,\text{s}$ (Immediate emergency brake required)
     - **WARNING (Level 1):** $1.5\,\text{s} < \text{TTC} \le 3.0\,\text{s}$ (Driver attention / prepare to brake)
     - **SAFE (Level 0):** $\text{TTC} > 3.0\,\text{s}$ (Normal driving headway)
   - Road surface adaptation: Multiplier expands thresholds on wet ($1.4\times$), gravel ($1.6\times$), or icy ($2.0\times$) surfaces.
   - Safety Rule: Edge Decision Tree ML classifier can augment risk, but **safety logic forbids downgrading a physics CRITICAL**.

---

## 6. How to Run It Today (Tested Commands)

| Step | Command | Result | Notes |
|---|---|---|---|
| 1. Unit Tests | `python -m pytest` | **PASS (20/20 passed)** | Fast (0.08s) unit test run |
| 2. Protocol Contract | `python validation/protocol_contract_test.py` | **PASS (6/6 passed)** | Telemetry schema passes |
| 3. Synthetic Eval | `python validation/evaluate_synthetic.py` | **PASS** | Generates evaluation plots in `validation/outputs/` |
| 4. Pin Consistency | `python validation/pin_validator.py` | **WARN (Non-critical)** | Pins 14/14 match diagram; constants `NUM_*_PINS` flagged as warnings |
| 5. Bridge Smoke Test | `"1000,120,30,2.40,2.20,2,0.85" \| python bridge\wokwi_serial_bridge.py --source stdin --no-launch-stack` | **PASS** | Packet parsed and forwarded cleanly |
| 6. Train Model | `python ml/training/train_model.py` | **PASS** | Trains RF (96.5% CV), DT (99.5%), exports C++ header |
| 7. Replay Runner | `python src/replay_runner.py` | **FAIL (Import error)** | Fails due to relative imports (`from alerts import ...`) |
| 8. Main Entrypoint | `python -m src.main` / `python src/main.py` | **FAIL (File does not exist)** | No centralized CLI / demo entry point |

---

## 7. Problems Found

### Critical (Broken or Blocks Running)
1. **Missing Top-Level / Package Entry Point:** No `src/main.py` or `main.py` exists to run an end-to-end demo directly. Users currently have to figure out how to run multi-window bat scripts.
2. **Inconsistent Imports in `src/`:** Modules like `src/replay_runner.py` use flat imports like `from alerts import check_and_alert` without sys.path fallback, causing `ModuleNotFoundError` when run from root or via `-m src.replay_runner`.

### Important (Messy structure, hardcoded paths, duplication)
1. **Duplicate `ml_classifier.h`:** Exists in both `firmware/ml_classifier/ml_classifier.h` and root `firmware/ml_classifier.h`.
2. **Deprecation Confusion in Firmware:** `firmware/config/config.h` has a large warning block noting pin conflicts with `firmware/pinmap.h`.
3. **No Direct Python TTC Kinematics in `src/` for Unit Testing:** TTC formulas are implemented in C++ (`ttc_engine.h`) and embedded in `serial_simulator.py` and `dashboard.py`, but missing from an isolated reusable math module like `src/ttc_engine.py` or `src/utils.py`.
4. **Bat Scripts Assume Fixed Path / Env Name:** `run_dashboard.bat` checks `.venv` and `ttc_env`, but fails if Python is global or venv has a custom name.

### Nice-to-Have
1. SVG visual diagram of the two-vehicle geometry (ego car, lead car, distance, closing speed).
2. Direct standalone script to generate nice demonstration result plots in `results/`.
3. Clean modern requirements.txt.

---

## 8. Existing Real & Reusable Results
- `validation/outputs/confusion_matrix.png`: Real confusion matrix from synthetic dataset evaluation.
- `validation/outputs/scenario_summary.png`: Real metrics breakdown across synthetic scenarios.
- `validation/outputs/timeline_summary.png`: Real timeline showing distance, speed, and TTC dynamics.
- `dataset/synthetic_ttc_validation.csv`: Real 610-row dataset spanning safe cruise, sudden braking, slow closing, and wet conditions.
