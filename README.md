# Adaptive Collision Risk Prediction System

## Time-to-Collision (TTC) Monitoring Dashboard

This project implements a real-time collision risk monitoring system based on the **Time-to-Collision (TTC)** safety metric.
The system integrates simulated or live telemetry data, a machine-learning risk classifier, and a Streamlit-based monitoring dashboard.

The objective is to demonstrate predictive collision warning logic that can be later integrated with embedded hardware (ESP32-based sensing system).

---

## Project Features

* Real-time TTC risk visualization dashboard
* Live telemetry data simulation for testing
* Serial data acquisition support for embedded hardware
* Machine-learning-based risk classification
* Continuous session logging for dataset generation
* Modular Python architecture for easy hardware integration

---

## Project Structure

```
TTC_Project/
│
├── run_dashboard.bat              One-click launcher (simulator + dashboard + browser)
├── requirements.txt               Python package dependencies
├── README.md                      Project documentation
├── .gitignore                     Git ignore rules
│
├── PYTHON/                        Source code
│   ├── dashboard.py               Streamlit monitoring dashboard
│   ├── serial_simulator.py        Simulated telemetry data generator
│   └── serial_reader.py           ESP32 serial data acquisition
│
├── MODELS/                        Machine learning
│   └── ml_model.pkl               Pre-trained Random Forest classifier
│
├── DATASET/                       Training data
│   └── ttc_dataset.csv            Dataset used during model training
│
├── NOTEBOOK/                      Research and development
│   └── ml_work.ipynb              Model training and evaluation notebook
│
├── LOGS/                          Runtime data (gitignored)
│   └── live_data.txt              Real-time telemetry log file
│
└── ttc_env/                       Python virtual environment (gitignored)
```

---

## System Workflow

```
Telemetry Source → Data Logging → ML Risk Classification → Dashboard Visualization
```

The dashboard continuously reads telemetry data and updates:

* TTC gauge
* Risk classification status
* Distance and velocity trends
* Session statistics

---

## Quick Start

### One-Click Launch

The fastest way to run the entire system:

**Option A — Double-click:**
> Double-click `run_dashboard.bat` in File Explorer. Done.

**Option B — From VS Code terminal:**
```powershell
cmd.exe /c run_dashboard.bat
```

This automatically:
1. Activates the virtual environment
2. Starts the telemetry simulator in a new terminal
3. Launches the Streamlit dashboard in a new terminal
4. Opens `http://localhost:8501` in your browser

---

## Manual Setup

### Environment Setup

Create and activate a Python virtual environment:

```powershell
python -m venv ttc_env
.\ttc_env\Scripts\Activate.ps1
```

Install project dependencies:

```powershell
pip install -r requirements.txt
```

---

### Running the Dashboard (Simulation Mode)

Open **two terminals**.

#### Terminal 1 — Start Telemetry Simulator

```powershell
python PYTHON/serial_simulator.py
```

This process continuously writes simulated telemetry data to `LOGS/live_data.txt`.

#### Terminal 2 — Launch Monitoring Dashboard

```powershell
streamlit run PYTHON/dashboard.py
```

After startup, open the local web URL displayed in the terminal:

```
http://localhost:8501
```

---

### Running with Real Hardware (Serial Mode)

1. Connect the embedded device (e.g., ESP32) via USB.
2. Update the serial port inside `PYTHON/serial_reader.py`:

```python
ser = serial.Serial("COM3", 115200, timeout=1)
```

3. Start serial data acquisition:

```powershell
python PYTHON/serial_reader.py
```

4. Launch the dashboard in a separate terminal:

```powershell
streamlit run PYTHON/dashboard.py
```

---

## Important Notes

* The dashboard expects telemetry log file at `LOGS/live_data.txt`.
* The simulator overwrites the file periodically to emulate live streaming.
* Real hardware mode requires continuous serial data transmission.
* This dashboard is part of a larger embedded safety prototype currently under development.

---

## Current Development Status

* Dashboard visualization module — Implemented
* Telemetry simulation framework — Implemented
* Serial communication module — Implemented
* One-click launcher — Implemented
* Embedded firmware integration — In progress
* Machine learning optimisation — In progress
* Experimental validation — Pending

---

## Technology Stack

* Python
* Streamlit
* NumPy / Pandas
* Scikit-learn
* PySerial
* Embedded IoT (ESP32 — integration stage)

---

## Intended Applications

* Forward collision warning systems
* Smart parking assistance
* Autonomous robot safety
* Industrial vehicle monitoring
* Driver behaviour research

---

## Author

Undergraduate Engineering Project
Automotive Safety and Embedded Systems Domain

---
