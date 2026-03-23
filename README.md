# TTC Collision Risk Monitoring System

A Python-based prototype for monitoring forward-collision risk using Time-to-Collision (TTC). The system combines distance and closing-speed telemetry, TTC-based physics logic, an optional machine-learning risk model, and a Streamlit dashboard for live visual monitoring.

The system runs in three modes:

- **Simulated** — fully synthetic, no hardware needed.
- **Log-driven** — reads the latest telemetry from a shared file.
- **Live serial** — reads directly from an ESP32 over USB.

## What the project does

For each telemetry update the system estimates how soon a collision would occur if the current approach continues.

| Risk level | Condition |
|------------|-----------|
| SAFE | TTC above 3.0 s |
| WARNING | TTC between 1.5 and 3.0 s |
| CRITICAL | TTC at or below 1.5 s |

The dashboard then shows current distance, speed, and TTC; current risk class; rolling trends; session statistics; and event/log information.

If a trained ML model is available it is used for risk prediction. Otherwise the dashboard falls back to TTC threshold logic so the system remains usable without the model.

## Current project state

The software side is functional for simulation and dashboard monitoring.

| Component | Status |
|-----------|--------|
| Simulation pipeline | Working |
| Dashboard UI | Working |
| ML inference | Integrated (when model file present) |
| Real hardware telemetry | Not yet validated |
| ESP32 field testing | Pending |

This means the project is currently a software prototype with hardware integration support already scaffolded.

## Repository layout

```
TTC-PROJECT-FILES/
├── README.md
├── requirements.txt
├── run_dashboard.bat
├── docs/
│   ├── understanding.md
│   ├── status.md
│   ├── serial_protocol.md
│   └── integration_status.md
├── src/
│   ├── dashboard.py
│   ├── serial_simulator.py
│   ├── serial_reader.py
│   ├── config.py
│   ├── alerts.py
│   ├── analytics.py
│   ├── logger.py
│   ├── safety_features.py
│   ├── utils.py
│   └── validators.py
├── MODELS/
├── LOGS/
└── ttc_env/
```

## Key files

| File | Purpose |
|------|---------|
| `src/dashboard.py` | Main Streamlit application. Supports Simulator, Live Log, and ESP32 Serial input modes. |
| `src/serial_simulator.py` | Generates synthetic TTC telemetry and writes it to `LOGS/live_data.txt`. |
| `src/serial_reader.py` | Reads 7-field serial packets from an ESP32 and writes the latest reading to `LOGS/live_data.txt` while saving full sessions to CSV. |
| `src/config.py` | Central configuration for thresholds, serial settings, simulator parameters, and logging. |
| `src/safety_features.py` | Hysteresis filtering, sensor fault detection, velocity sanity checks, and ML-confidence fusion. |
| `MODELS/` | Location for the trained model file (`ml_model.pkl`). |
| `LOGS/` | Runtime output: latest live telemetry file and saved session logs. |

## Data flow

1. Telemetry is produced by either the simulator, the live log file, or an ESP32 serial connection.
2. The dashboard validates and interprets the incoming values.
3. Risk is determined using the ML model when available, otherwise TTC threshold fallback logic is used.
4. The interface updates the live status, trends, counts, and session metrics.

## Requirements

The main dependencies are:

- `pyserial`
- `pandas`
- `numpy`
- `streamlit`
- `scikit-learn==1.7.1`
- `joblib`

Install with:

```
pip install -r requirements.txt
```

## Setup

### Option 1 — Use the existing virtual environment

PowerShell:

```powershell
.\ttc_env\Scripts\Activate.ps1
```

Command Prompt:

```cmd
ttc_env\Scripts\activate.bat
```

### Option 2 — Create a new virtual environment

```
python -m venv ttc_env
ttc_env\Scripts\activate
pip install -r requirements.txt
```

## Running the project

### One-click launcher (fastest)

```
run_dashboard.bat
```

This activates the virtual environment, opens the simulator in one terminal, opens the Streamlit dashboard in another, and opens the browser at `http://localhost:8501`.

### Manual run — Simulator plus dashboard

Terminal 1:

```
python src\serial_simulator.py
```

Terminal 2:

```
streamlit run src\dashboard.py --server.headless true
```

Then open `http://localhost:8501`.

Inside the dashboard use Simulator mode for in-process synthetic data, or Live Log mode to read from the file updated by `serial_simulator.py`.

### Manual run — ESP32 serial mode

List available ports:

```
python src\serial_reader.py --list
```

Start the serial reader:

```
python src\serial_reader.py --port COM3
```

In another terminal start the dashboard:

```
streamlit run src\dashboard.py --server.headless true
```

The dashboard can then use ESP32 Serial mode for direct USB reads or Live Log mode to read the file written by `serial_reader.py`.

## Telemetry format

Both the simulator and serial reader use a 7-field CSV format:

```
timestamp_ms,distance_cm,speed_kmh,ttc_basic,ttc_ext,risk_class,confidence
```

| Position | Field | Unit | Meaning |
|----------|-------|------|---------|
| 1 | `timestamp_ms` | ms | Sample timestamp |
| 2 | `distance_cm` | cm | Current obstacle distance |
| 3 | `speed_kmh` | km/h | Closing speed |
| 4 | `ttc_basic` | s | TTC using constant-speed model |
| 5 | `ttc_ext` | s | TTC using deceleration-aware model |
| 6 | `risk_class` | — | `0` = SAFE, `1` = WARNING, `2` = CRITICAL |
| 7 | `confidence` | 0–1 | Confidence score |

## Configuration

Most settings live in `src/config.py`:

- TTC risk thresholds
- Dashboard refresh interval
- Serial baud rate and timeout
- Simulator starting distance and loop timing
- Logging behaviour

Default thresholds: CRITICAL ≤ 1.5 s, WARNING ≤ 3.0 s, SAFE > 3.0 s.

## Logs and outputs

Runtime files are written to `LOGS/`:

| File | Description |
|------|-------------|
| `LOGS/live_data.txt` | Latest telemetry sample for dashboard polling |
| `LOGS/session_*.csv` | Full session exports created by `serial_reader.py` |
| `LOGS/ttc_system.log` | Application log file when logging is enabled |

## Notes and limitations

- The dashboard is usable without hardware.
- The ML path depends on a compatible model file being present in `MODELS/`.
- `scikit-learn==1.7.1` is pinned because the model loader checks for that version.
- Real-world validation, sensor calibration, and firmware-side filtering are still pending.
- Hardware integration support exists in the code but full system verification depends on actual ESP32 and sensor testing.

## Further documentation

| Document | Description |
|----------|-------------|
| `docs/understanding.md` | Simple explanation of TTC logic and system flow |
| `docs/status.md` | Current project progress, blockers, and roadmap |
| `docs/serial_protocol.md` | Exact telemetry packet format expected by the Python side |
| `docs/integration_status.md` | Hardware-integration checklist and handoff status |

## Recommended first run

1. Activate the environment.
2. Run `run_dashboard.bat`.
3. Confirm the dashboard opens in the browser.
4. Read `docs/understanding.md` for the system logic.
5. Read `docs/status.md` for current progress and remaining hardware work.
6. Use `docs/serial_protocol.md` before writing or changing ESP32 firmware.
