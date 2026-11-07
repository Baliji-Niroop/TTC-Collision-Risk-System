# PLAN: TTC Collision Risk System 10/10 Modernization

**Date:** 2026-11-07  
**Branch:** `docs/10-out-of-10-cleanup`  
**Goal:** Deliver a professional, beginner-friendly, clean, 10/10 automotive engineering showcase without introducing unnecessary complexity.

---

## 1. Target Folder Structure

```text
TTC-Collision-Risk-System/
├── README.md                          <- Main showpiece (concise, clear, <300 lines)
├── LICENSE                            <- MIT License (existing)
├── requirements.txt                   <- Pinned runtime dependencies
├── requirements-dev.txt               <- Developer & testing dependencies
├── .gitignore                         <- Comprehensive gitignore (venv, cache, temporary logs)
├── TTC.ino                            <- Arduino IDE root sketch (existing)
├── diagram.json                       <- Wokwi wiring diagram (existing)
├── wokwi.toml                         <- Wokwi project config (existing)
├── run_dashboard.bat                  <- Windows dashboard stack launcher
├── run_wokwi_bridge.bat               <- Windows Wokwi bridge launcher
├── src/                               <- Clean, robust Python source modules
│   ├── __init__.py                    <- Package init
│   ├── main.py                        <- SINGLE ENTRY POINT: runs end-to-end demo & replay
│   ├── ttc_engine.py                  <- Reusable core TTC math & physics calculation functions
│   ├── config.py                      <- Central configuration and thresholds
│   ├── alerts.py                      <- Alert management and throttling
│   ├── analytics.py                   <- Driving insights and TTC statistics
│   ├── dashboard.py                   <- Streamlit live dashboard UI
│   ├── logger.py                      <- Logging utility
│   ├── replay_runner.py               <- Fixed imports; session replayer
│   ├── safety_features.py             <- Hysteresis & multi-sensor safety fusion
│   ├── serial_reader.py               <- Hardware serial receiver
│   ├── serial_simulator.py            <- Synthetic serial streamer
│   ├── telemetry_schema.py            <- 7-field telemetry contract serialization/parsing
│   ├── utils.py                       <- Environment & file helpers
│   └── validators.py                  <- Packet and anomaly validation
├── data/                              <- Renamed/linked from dataset/ with a clear README
│   ├── README.md                      <- Explains synthetic kinematic dataset structure
│   └── synthetic_ttc_validation.csv   <- 610-sample kinematic test dataset
├── firmware/                          <- Embedded ESP32 runtime
│   ├── main.ino                       <- Firmware loop & setup
│   ├── pinmap.h                       <- Single source of truth for GPIO mappings
│   ├── config/                        <- Config and protocol headers
│   ├── ml/                            <- Firmware TTC engine
│   ├── alerts/                        <- OLED and alert handling
│   ├── sensors/                       <- Sensor drivers
│   └── ml_classifier/                 <- Exported decision tree header
├── hardware/                          <- Assembly checklist, wiring guides, BOM
├── results/                           <- Real, re-generable output plots and metrics
│   ├── README.md                      <- Explanation of real plots
│   ├── generate_plots.py              <- Standalone script to reproduce all result figures
│   ├── ttc_vs_time.png                <- Real TTC timeline with risk threshold lines
│   ├── risk_distribution.png          <- Bar chart of driving time per risk class
│   └── confusion_matrix.png           <- Real classification evaluation
├── tests/                             <- Simple, bulletproof pytest unit tests
│   ├── conftest.py
│   ├── test_ttc_engine.py             <- Tests core TTC logic (normal, moving away, static, edge cases)
│   ├── test_analytics.py              <- Tests risk classification thresholds
│   ├── test_config.py                 <- Tests configuration constants
│   └── test_validators.py             <- Tests telemetry validation
└── docs/                              <- Detailed, clear documentation
    ├── architecture.md                <- System architecture & data flow
    ├── how-it-works.md                <- Kinematics, TTC formulas, and worked examples
    ├── usage.md                       <- Step-by-step beginner guide + troubleshooting
    ├── project-journey.md             <- Chronological engineering story (problem -> solution)
    ├── serial_protocol.md             <- 7-field serial protocol contract
    └── images/                        <- Diagrams and figures
        ├── vehicle_geometry.svg       <- Clean, hand-crafted SVG showing ego, lead car, and TTC
        └── system_pipeline.png / svg
```

---

## 2. List of Files to Create, Edit, or Clean

### A) Code & Structure Changes
1. **Create `src/ttc_engine.py`:**
   - Pure, standalone implementation of `compute_ttc_basic(distance_m, v_closing_ms)` and `compute_ttc_extended(distance_m, v_closing_ms, decel_ms2)`.
   - Comprehensive docstrings with units ($m$, $m/s$, $s$), edge case handling ($v \le 0$, negative distance).
2. **Create `src/main.py`:**
   - Single clean CLI entry point supporting:
     - `python src/main.py --demo` (runs simulated scenario, prints live telemetry, generates plots)
     - `python src/main.py --replay data/synthetic_ttc_validation.csv`
     - `python src/main.py --dashboard` (launches Streamlit dashboard)
     - `python src/main.py --check` (runs all validation gates)
3. **Fix Imports in `src/replay_runner.py`, `src/serial_simulator.py`, `src/dashboard.py`:**
   - Support both direct script execution (`python src/replay_runner.py`) and module execution (`python -m src.replay_runner`).
4. **Remove Redundant Files:**
   - Remove duplicate `firmware/ml_classifier.h` (the authoritative one lives in `firmware/ml_classifier/ml_classifier.h`).
5. **Create `data/`:**
   - Ensure beginner-friendly data directory layout with `data/README.md`. Keep `dataset/` pointing/symlinking or keep backward compatibility so existing scripts work seamlessly.
6. **Create `results/generate_plots.py`:**
   - Generates authentic PNG plots from `dataset/synthetic_ttc_validation.csv` with clear units, titles, legends, and risk zone backgrounds.
7. **Create `tests/test_ttc_engine.py`:**
   - 6 tests for core TTC logic: normal case, zero closing speed, lead vehicle moving away (diverging), already colliding ($d \le 0$), deceleration model stops in time, deceleration model collision.

### B) Documentation
1. **`README.md`:** Complete rewrite strictly following the 15-section template (<300 lines, beginner-friendly, working badges, worked TTC calculation example).
2. **`docs/how-it-works.md`:** Comprehensive explanation of TTC kinematics, sensor fusion, edge cases, and decision rules.
3. **`docs/architecture.md`:** System architecture, component interaction, and hardware-software data flow.
4. **`docs/usage.md`:** Step-by-step setup, running via CLI / GUI / Wokwi, and troubleshooting matrix.
5. **`docs/project-journey.md`:** The chronological journey from capstone problem statement to edge-AI ADAS implementation.
6. **`docs/images/vehicle_geometry.svg`:** Hand-crafted, crisp SVG showing two vehicles (ego vehicle, lead vehicle), relative distance $d$, speeds $v_{\text{ego}}$ and $v_{\text{lead}}$, and closing velocity $v_{\text{closing}}$.

---

## 3. Diagrams to Produce
1. **System Pipeline Flowchart (Mermaid):** Sensors $\to$ Firmware Filter $\to$ TTC Calculation $\to$ Risk Classification $\to$ Outputs (OLED/LED/Buzzer) & Serial Telemetry $\to$ Python Dashboard / Analytics.
2. **Architecture / Module Flow Diagram (Mermaid):** Shows caller-callee relationship between `main.py`, `serial_reader.py`, `ttc_engine.py`, `validators.py`, and `alerts.py`.
3. **Risk Decision State Diagram (Mermaid):** Safe ($>3.0\text{s}$), Warning ($1.5 - 3.0\text{s}$), Critical ($\le 1.5\text{s}$) with road condition adjustments.
4. **Vehicle Kinematics Geometry Diagram (SVG):** Custom vector drawing illustrating the physical scenario.
5. **Runtime Sequence Diagram (Mermaid):** Sensor polling $\to$ estimation $\to$ telemetry output $\to$ dashboard visualization.
