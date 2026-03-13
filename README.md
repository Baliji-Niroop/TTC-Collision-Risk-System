# TTC Project (Time-to-Collision Dashboard)

This project demonstrates a simple collision risk monitoring dashboard using Streamlit, a pre-trained ML model, and live telemetry data.

## What’s Included

- `dashboard.py`: Streamlit dashboard that reads `live_data.txt` and displays TTC risk stats.
- `serial_simulator.py`: Generates simulated live data into `live_data.txt`.
- `serial_reader.py`: Reads serial data from a device (e.g., ESP32) on `COM3`.
- `ml_model.pkl`: Pre-trained scikit-learn model used by the dashboard.
- `ttc_dataset.csv`: Dataset generated during model training.
- `ml_work.ipynb`: Notebook used to create and evaluate the model.

## Setup

1. Create and activate a Python environment (recommended):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

## Running the Dashboard (Simulated Data)

1. Start the data simulator in a separate terminal:

```powershell
python serial_simulator.py
```

2. Launch Streamlit:

```powershell
streamlit run dashboard.py
```

## Running with Real Serial Data

1. Update `serial_reader.py` to use the correct COM port.
2. Run it:

```powershell
python serial_reader.py
```

3. Launch the Streamlit dashboard in a separate terminal.

## Notes

- The dashboard expects `live_data.txt` to be in the same folder as `dashboard.py`.
- The simulator overwrites `live_data.txt` at ~3Hz.
