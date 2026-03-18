# TTC Collision Risk Monitoring System

This project is a Python-based prototype for monitoring forward-collision risk using Time-to-Collision (TTC). It combines:

- distance and closing-speed telemetry,
- TTC-based physics logic,
- an optional machine-learning risk model,
- a Streamlit dashboard for live visual monitoring.

The system can run in three practical modes:

- fully simulated, with no hardware required,
- log-driven, by reading the latest telemetry from a shared file,
- live serial, by reading directly from an ESP32 over USB.

## What The Project Does

For each telemetry update, the system estimates how soon a collision would occur if the current approach continues.

- `SAFE`: TTC above 3.0 s
- `WARNING`: TTC between 1.5 s and 3.0 s
- `CRITICAL`: TTC at or below 1.5 s

The dashboard then shows:

- current distance, speed, and TTC,
- current risk class,
- rolling trends,
- session statistics,
- event/log information.

If the trained ML model is available, it is used for risk prediction. If not, the dashboard falls back to TTC threshold logic so the system remains usable.

## Current Project State

The software side is functional for simulation and dashboard monitoring.

- Simulation pipeline: working
- Dashboard UI: working
- ML inference: integrated when model file is available
- Real hardware telemetry: not yet fully validated
- ESP32-based field testing: still pending

This means the project is currently best treated as a software prototype with hardware integration support already scaffolded.

## Repository Layout

```text
TTC-PROJECT-FILES/
├── README.md
├── requirements.txt
├── run_dashboard.bat
├── status.md
├── understanding.md
├── LOGS/
├── MODELS/
├── PYTHON/
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
└── ttc_env/
```

## Key Files

- `PYTHON/dashboard.py`: Main Streamlit application. Supports Simulator, Live Log, and ESP32 Serial input modes.
- `PYTHON/serial_simulator.py`: Generates synthetic TTC telemetry and writes it to `LOGS/live_data.txt`.
- `PYTHON/serial_reader.py`: Reads 7-field serial packets from an ESP32 and writes the latest reading to `LOGS/live_data.txt` while also saving full sessions to CSV.
- `PYTHON/config.py`: Central configuration for thresholds, serial settings, simulator parameters, and logging.
- `PYTHON/safety_features.py`: Extra safety logic such as hysteresis filtering, sensor fault detection, velocity sanity checks, and ML-confidence fusion.
- `MODELS/`: Intended location for the trained model file, typically `ml_model.pkl`.
- `LOGS/`: Runtime output, including the latest live telemetry file and saved session logs.

## Data Flow

The project follows this basic pipeline:

1. Telemetry is produced by either the simulator, the live log file, or an ESP32 serial connection.
2. The dashboard validates and interprets the incoming values.
3. Risk is determined using the ML model when available, otherwise TTC threshold fallback logic is used.
4. The interface updates the live status, trends, counts, and session metrics.

## Requirements

The repository already includes a virtual environment folder, but if you need to set up the project yourself, the main dependencies are:

- `pyserial`
- `pandas`
- `numpy`
- `streamlit`
- `scikit-learn==1.7.1`
- `joblib`

You can install them with:

```cmd
pip install -r requirements.txt
```

## Setup

### Option 1: Use the existing virtual environment

On Windows PowerShell:

```powershell
.\ttc_env\Scripts\Activate.ps1
```

On Command Prompt:

```cmd
ttc_env\Scripts\activate.bat
```

### Option 2: Create a new virtual environment

```cmd
python -m venv ttc_env
ttc_env\Scripts\activate
pip install -r requirements.txt
```

## Running The Project

### Fastest Start: One-click launcher

The simplest way to run the project is:

```cmd
run_dashboard.bat
```

This script:

- activates the virtual environment,
- opens the simulator in one terminal,
- opens the Streamlit dashboard in another terminal,
- opens the browser at `http://localhost:8501`.

Use this mode if you want to see the project working immediately without hardware.

### Manual Run: Simulator + Dashboard

Open two terminals in the project root.

Terminal 1:

```cmd
python PYTHON\serial_simulator.py
```

Terminal 2:

```cmd
streamlit run PYTHON\dashboard.py --server.headless true
```

Then open:

```text
http://localhost:8501
```

Inside the dashboard, use either:

- `Simulator` mode for in-process synthetic data, or
- `Live Log` mode if you want the dashboard to read the file being updated by `serial_simulator.py`.

### Manual Run: ESP32 Serial Mode

If you have an ESP32 sending valid telemetry over USB, first list available ports:

```cmd
python PYTHON\serial_reader.py --list
```

Then start the serial reader:

```cmd
python PYTHON\serial_reader.py --port COM3
```

In another terminal, start the dashboard:

```cmd
streamlit run PYTHON\dashboard.py --server.headless true
```

The dashboard can then use:

- `ESP32 Serial` mode for direct USB reads, if `pyserial` is installed, or
- `Live Log` mode to read the latest line written by `serial_reader.py`.

## Telemetry Format

The simulator and serial reader both use the same 7-field comma-separated format:

```text
timestamp_ms,distance_cm,speed_kmh,ttc_basic,ttc_ext,risk_class,confidence
```

Meaning:

- `timestamp_ms`: sample timestamp in milliseconds
- `distance_cm`: measured obstacle distance in centimeters
- `speed_kmh`: closing speed in km/h
- `ttc_basic`: TTC from the constant-speed model
- `ttc_ext`: TTC from the extended deceleration-aware model
- `risk_class`: `0 = SAFE`, `1 = WARNING`, `2 = CRITICAL`
- `confidence`: confidence score used for display/monitoring

## Configuration

Most important settings live in `PYTHON/config.py`, including:

- TTC risk thresholds
- dashboard refresh interval
- serial baud rate and timeout
- simulator starting distance and loop timing
- logging behavior

Default TTC thresholds are:

- `CRITICAL`: `<= 1.5 s`
- `WARNING`: `<= 3.0 s`
- `SAFE`: `> 3.0 s`

## Logs And Outputs

The project writes runtime files to `LOGS/`.

- `LOGS/live_data.txt`: latest telemetry sample for dashboard polling
- `LOGS/session_*.csv`: full session exports created by `serial_reader.py`
- `LOGS/ttc_system.log`: application log file when logging is enabled

## Notes And Limitations

- The dashboard is usable without hardware.
- The ML path depends on a compatible model file being present in `MODELS/`.
- `scikit-learn==1.7.1` is pinned because the model loader checks for that version.
- Real-world validation, sensor calibration, and firmware-side filtering are still pending.
- Hardware integration support exists in the code, but full system verification depends on actual ESP32 and sensor testing.

## Additional Documentation

- `understanding.md`: simple explanation of the TTC logic and system flow
- `status.md`: current project progress, blockers, and roadmap tracking
- `SERIAL_PROTOCOL.md`: exact telemetry packet format expected by the Python side
- `INTEGRATION_STATUS.md`: hardware-integration checklist and current handoff status

## Recommended First Run

If you are opening this repository for the first time, use this order:

1. Activate the environment.
2. Run `run_dashboard.bat`.
3. Confirm the dashboard opens in the browser.
4. Read `understanding.md` for the system logic.
5. Read `status.md` for current progress and remaining hardware work.
6. Use `SERIAL_PROTOCOL.md` before writing or changing ESP32 firmware.
