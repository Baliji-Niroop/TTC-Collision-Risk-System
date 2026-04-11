# TTC Project Organization Guide

**Last Updated:** April 11, 2026  
**Version:** 1.0  
**Status:** Organized & Ready for Hardware Deployment

---

## Directory Structure Overview

```
TTC/
├── firmware/                    # Arduino/ESP32 firmware
│   ├── config/
│   │   ├── config.h             # All system configuration & thresholds
│   │   ├── arduino_compat.h     # Arduino compatibility layer
│   │   ├── kalman_filter.h      # Signal smoothing
│   │   └── ...
│   ├── sensors/
│   │   ├── sensors.h            # Sensor interface (HC-SR04, encoder, MPU6050)
│   │   ├── sensor_drivers.h     # Low-level sensor drivers
│   │   └── ...
│   ├── alerts/
│   │   ├── risk_classifier.h    # Risk classification logic
│   │   ├── alert_controller.h   # LED/buzzer control
│   │   └── ...
│   ├── ml_classifier/           # Optional ML decision tree
│   ├── pinmap.h                 # SINGLE SOURCE OF TRUTH for pin assignments
│   └── main.ino                 # Main firmware entry point
│
├── src/                         # Python backend
│   ├── config.py                # System configuration (thresholds, paths)
│   ├── logger.py                # Logging utilities
│   ├── dashboard.py             # Streamlit UI (run with: streamlit run src/dashboard.py)
│   ├── serial_reader.py         # Read telemetry from hardware
│   ├── serial_simulator.py      # Simulate vehicle data (for testing)
│   ├── telemetry_schema.py      # 7-field telemetry packet definition
│   ├── validators.py            # Telemetry validation
│   ├── alerts.py                # Alert engine
│   ├── analytics.py             # Session analytics
│   ├── replay_runner.py         # Replay stored sessions
│   └── ...
│
├── bridge/                      # Wokwi simulation bridge
│   ├── wokwi_serial_bridge.py   # Converts stdin/websocket → telemetry → dashboard
│   └── ...
│
├── ml/                          # Machine learning (optional)
│   ├── inference/
│   │   └── __init__.py          # ML model loading & inference
│   ├── training/
│   │   └── train_model.py       # Training script (if using ML)
│   └── ...
│
├── validation/                  # Test & validation suite
│   ├── protocol_contract_test.py    # Telemetry format validation (6 tests, all pass)
│   ├── evaluate_synthetic.py        # Classification accuracy test (100% pass)
│   ├── pin_validator.py             # Pin sync check (14/14 pins verified)
│   ├── compare_wokwi_baseline.py    # Wokwi vs real hardware comparison
│   ├── capture_demo_evidence.py     # Record evidence sessions
│   └── outputs/
│       └── [test results & reports]
│
├── docs/                        # Documentation
│   ├── README.md                # Project overview
│   ├── serial_protocol.md       # Telemetry packet spec (7-field format)
│   ├── hardware_wiring_guide.md # CRITICAL: Pin assignments, breadboard layout, resistor values
│   ├── wokwi_bridge_smoke_test.md  # Wokwi simulation setup
│   ├── PROJECT_STRUCTURE.md     # Architecture overview
│   ├── PROJECT_MAP.md           # File-by-file walkthrough
│   ├── QUICK_START.txt          # Quick reference
│   ├── archive/
│   │   └── [historical docs, session artifacts]
│   ├── diagrams/
│   │   └── [architecture diagrams]
│   ├── guides/
│   │   └── [step-by-step guides]
│   └── api/
│       └── [API documentation]
│
├── build/                       # Compiled firmware binaries (gitignored)
│   ├── TTC.ino.bin             # ESP32 binary (export from Arduino IDE)
│   ├── TTC.ino.elf             # ESP32 ELF debug file
│   └── .gitkeep                # Directory marker
│
├── LOGS/                        # Runtime logs (gitignored)
│   ├── live_data.txt           # Current session telemetry
│   ├── ttc_system.log          # System logs
│   └── archive/
│       └── [session backups]
│
├── MODELS/                      # ML models (gitignored)
│   └── ml_model.pkl            # Trained classifier (optional)
│
├── config/                      # Project config
│   ├── __init__.py             # Re-exports from src/config (for import compatibility)
│   └── requirements.txt         # Python dependencies
│
├── dataset/                     # Training/validation datasets
│   ├── raw/                    # Original sensor recordings
│   ├── processed/              # Cleaned/normalized (gitignored)
│   └── exports/                # Export formats (gitignored)
│
├── tests/                       # Unit tests
│   └── [pytest test files]
│
├── .github/                     # GitHub workflows
│   ├── workflows/
│   │   └── [CI/CD pipelines]
│   └── ...
│
├── .vscode/                     # VS Code settings
├── .venv/                       # Python virtual environment (gitignored)
├── .gitignore                   # Git ignore patterns
├── wokwi.toml                   # Wokwi simulator config (points to build/TTC.ino.bin)
├── diagram.json                 # Hardware circuit diagram
├── TTC.ino                       # Symlink to firmware/main.ino (for Arduino IDE)
├── README.md                    # Project README
└── [batch files for launching]
    ├── run_dashboard.bat        # Start dashboard + simulator
    ├── run_wokwi_bridge.bat     # Start bridge for Wokwi
    └── run_stdin_test.bat       # Test bridge with stdin
```

---

## Key Files & Their Purpose

### Configuration (Single Source of Truth)
| File | Purpose | Update When |
|------|---------|------------|
| `firmware/pinmap.h` | **ESP32 pin assignments** | Adding new hardware component |
| `firmware/config/config.h` | Thresholds, timings, sensor constants | Tuning system behavior |
| `src/config.py` | Python config mirroring firmware | Keeping sync with firmware |
| `wokwi.toml` | Wokwi simulator setup | Changing binary format |

### Documentation (Read First)
| File | Content | When to Read |
|------|---------|------------|
| `README.md` | Project overview & quick start | Starting the project |
| `docs/hardware_wiring_guide.md` | **CRITICAL for hardware** | Before buying/wiring components |
| `docs/serial_protocol.md` | Telemetry packet format | Understanding data flow |
| `docs/PROJECT_MAP.md` | File-by-file architecture | Exploring codebase |

### Firmware Entry Points
| File | Purpose |
|------|---------|
| `TTC.ino` | Symlink to `firmware/main.ino` (so Arduino IDE finds it) |
| `firmware/main.ino` | Main firmware loop, sensor reads, packet emission |
| `firmware/config/config.h` | All #defines and feature flags |

### Python Entry Points
| Script | Purpose | Run With |
|--------|---------|----------|
| `src/dashboard.py` | Real-time UI with metrics/alerts | `streamlit run src/dashboard.py` |
| `src/serial_reader.py` | Read telemetry from hardware serial port | `python src/serial_reader.py --port COMx` |
| `src/replay_runner.py` | Replay stored CSV sessions | `python src/replay_runner.py --input LOGS/session_*.csv` |
| `bridge/wokwi_serial_bridge.py` | Bridge stdin/websocket to telemetry | `echo "..." \| python bridge/wokwi_serial_bridge.py --source stdin` |

### Validation & Testing
| Script | Tests | Run With | Expected Result |
|--------|-------|----------|-----------------|
| `validation/protocol_contract_test.py` | Telemetry format (6 tests) | `python validation/protocol_contract_test.py` | ✅ 6/6 pass |
| `validation/evaluate_synthetic.py` | Classification accuracy (610 samples) | `python validation/evaluate_synthetic.py` | ✅ 100% accuracy |
| `validation/pin_validator.py` | Pin sync (14 pins) | `python validation/pin_validator.py` | ✅ 14/14 match |

---

## Import Paths Explained

### Python Imports
```python
# These all work (from any directory):
from config import RISK_LABELS, RISK_THRESHOLDS
from src.config import MODEL_PATH, LOG_DIR
from src.logger import get_logger
from src.validators import validate_csv_line
from src.alerts import check_and_alert
from src.telemetry_schema import parse_packet
```

**How it works:**
- `config/` package re-exports symbols from `src/config.py` (explicit imports, no wildcard)
- Allows imports like `from config import X` from any directory
- Replaces old fragile wildcard import pattern

### Firmware Includes
```cpp
// All these work in Arduino IDE:
#include "config/config.h"        // All settings
#include "pinmap.h"               // Pin assignments
#include "sensors/sensors.h"      // Sensor interface
#include "alerts/risk_classifier.h"
#include "ml_classifier/ml_classifier.h"
```

---

## Workflow: Common Tasks

### Task 1: Adjust TTC Thresholds
1. Edit `firmware/config/config.h`:
   ```cpp
   #define TTC_CRITICAL_S 1.5   // seconds
   #define TTC_WARNING_S 3.0    // seconds
   ```
2. Edit `src/config.py` to match:
   ```python
   RISK_THRESHOLDS = {
       "critical": 1.5,
       "warning": 3.0,
   }
   ```
3. Recompile firmware & restart Python side

### Task 2: Add New Hardware Component
1. Add pin definition to `firmware/pinmap.h`:
   ```cpp
   static const uint8_t PIN_NEW_SENSOR = 33;
   ```
2. Update `docs/hardware_wiring_guide.md` with wiring instructions
3. Update `firmware/config/config.h` if adding new feature flags
4. Recompile firmware

### Task 3: Run Full Validation Suite
```bash
# Test telemetry protocol
python validation/protocol_contract_test.py

# Test classification accuracy
python validation/evaluate_synthetic.py

# Test pin sync
python validation/pin_validator.py

# All must pass ✅
```

### Task 4: Deploy to Real Hardware
1. Export compiled binary from Arduino IDE → `build/TTC.ino.bin`
2. Connect ESP32 via USB
3. Upload in Arduino IDE (Ctrl+U)
4. Start dashboard: `python src/dashboard.py`
5. Start serial reader: `python src/serial_reader.py --port COMx`

---

## Dependency Map

### Firmware Dependencies
```
main.ino
  ├── config/config.h (feature flags, thresholds)
  ├── pinmap.h (pin assignments)
  ├── sensors/sensors.h (sensor interface)
  ├── ml/ttc_engine.h (TTC calculation)
  ├── alerts/risk_classifier.h (risk logic)
  ├── ml_classifier/ml_classifier.h (optional ML)
  └── Arduino libraries (Wire.h, Adafruit_MPU6050, Adafruit_SSD1306)
```

### Python Dependencies
```
dashboard.py
  ├── config (thresholds, paths)
  ├── logger (logging)
  ├── validators (telemetry checks)
  ├── telemetry_schema (packet format)
  ├── alerts (alert engine)
  ├── analytics (session analysis)
  └── External: streamlit, pandas, matplotlib
```

### Validation Dependencies
```
validation/
  ├── protocol_contract_test.py
  │   └── src/validators.py
  ├── evaluate_synthetic.py
  │   └── src/config.py, validators.py, telemetry_schema.py
  └── pin_validator.py
      ├── firmware/pinmap.h (parsed)
      └── diagram.json (parsed)
```

---

## Gitignore Verification

✅ **Properly Ignored:**
- `.venv/`, `ttc_env/` — virtual environments
- `__pycache__/`, `*.pyc` — Python cache
- `LOGS/*.csv`, `LOGS/live_data.txt` — session data
- `MODELS/*.pkl` — ML models
- `build/*.bin`, `build/*.elf` — compiled binaries
- `.env`, `secrets.json`, `config.json` — sensitive files

✅ **Properly Tracked:**
- `firmware/`, `src/`, `validation/`, `docs/` — source code
- `config/requirements.txt` — dependencies
- `README.md`, `wokwi.toml`, `diagram.json` — configuration

---

## Session Artifacts & Archive

Files created during development sessions are archived to `docs/archive/`:

| Artifact | Purpose | Location |
|----------|---------|----------|
| `IMPLEMENTATION_COMPLETE.md` | Firmware fix summary | Session workspace |
| `VALIDATION_REPORT.md` | Full test results | Session workspace |
| `plan.md` | Implementation plan | Session workspace |

These can be reviewed for history but aren't part of the main project.

---

## Next Phase: Hardware Deployment

When ready to purchase and assemble hardware:

1. **Review** `docs/hardware_wiring_guide.md` (complete with resistor values, I2C topology)
2. **Buy components** per component list (pinmap.h is source of truth)
3. **Wire on breadboard** exactly per pinmap.h pin assignments
4. **Export Arduino binary** and place in `build/`
5. **Upload firmware** via Arduino IDE
6. **Run Python side** and verify telemetry flowing

All documentation is in place. **Project is ready for hardware deployment.**

---

**Organized by:** Copilot  
**Date:** April 11, 2026  
**Status:** ✅ Clean & Ready
