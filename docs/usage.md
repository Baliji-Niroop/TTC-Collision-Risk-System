# Usage & Running Guide

This guide provides step-by-step instructions to set up, run, validate, and test the TTC Collision Risk System on your machine.

---

## 1. Prerequisites

- **Operating System:** Windows, Linux, or macOS.
- **Python:** Python 3.10 to 3.15 installed.
- **Optional (Hardware/Simulation):**
  - ESP32 development board (DevKit-V1) or a web browser to run the Wokwi simulation.
  - Arduino IDE (if flashing physical microcontroller).

---

## 2. Environment Setup

### Windows
```bat
run_dashboard.bat
```
The launcher uses an existing `.venv` or `ttc_env`; if neither exists, it creates
`ttc_env` and installs the runtime requirements.
To set up the environment manually instead:
```bat
py -3 -m venv ttc_env
ttc_env\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

### Linux / macOS
```bash
python3 -m venv ttc_env
source ttc_env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

---

## 3. Quick Run Options (Single Entry Point)

The system provides a central CLI entry point: `python src/main.py`.

### A) Run the Live Terminal Demo (No hardware needed)
Simulates a vehicle approaching an obstacle in real time and displays dynamic TTC calculations, closing speeds, and risk alerts:
```bash
python src/main.py --demo
```

### B) Replay Recorded or Synthetic Driving Data
Replays a recorded driving session CSV through the validation and analytics engine:
```bash
python src/main.py --replay data/synthetic_ttc_validation.csv
```

### C) Launch the Interactive Web Dashboard
Launches the full real-time Streamlit dashboard with live gauges, alert monitors, and dynamic charts:
```bash
python src/main.py --dashboard
```
*(Or on Windows, simply double-click `run_dashboard.bat`)*

### D) Run the System Quality & Verification Gate
Runs pytest, telemetry protocol checks, and pin mapping verification in a single command:
```bash
python src/main.py --check
```

---

## 4. Running with Hardware (ESP32)

1. Connect your ESP32 board to your computer via USB.
2. In Arduino IDE:
   - Open `TTC.ino`.
   - Select Board: **ESP32 Dev Module**.
   - Select your USB COM port.
   - Click **Upload**.
3. Launch the Python serial reader to capture real-time telemetry from the vehicle:
   ```bash
   python src/serial_reader.py --port COM3
   ```
   *(Replace `COM3` with your actual port, or run without `--port` to auto-detect)*

---

## 5. Running with Wokwi Simulation

1. Open [Wokwi](https://wokwi.com) in your browser and open `diagram.json` alongside `firmware/main.ino`.
2. Start the Wokwi serial bridge to feed simulated telemetry into your local Python dashboard:
   ```bash
   python bridge/wokwi_serial_bridge.py
   ```
   *(Or on Windows, double-click `run_wokwi_bridge.bat`)*

---

## 6. Regenerating Results & Plots

To regenerate the benchmark plots saved in `results/`:
```bash
python results/generate_plots.py
```

To retrain the cloud Random Forest model and edge Decision Tree (and export the C++ header for ESP32):
```bash
python ml/training/train_model.py
```

---

## 7. Troubleshooting Matrix

| Problem | Cause | Solution |
|---|---|---|
| Dashboard launcher reports that Python is missing | Python or the Python Launcher is not on `PATH` | Install Python 3 and enable the Python Launcher or add `python.exe` to `PATH`, then run `run_dashboard.bat` again |
| Dashboard dependencies fail to install | Network or package installation issue | Check your internet connection and rerun `run_dashboard.bat`; the launcher installs `requirements.txt` in the selected virtual environment when needed |
| `ModuleNotFoundError: No module named 'src'` | Running from subfolder or missing python path | Run commands from project root or use `python -m src.main` |
| Streamlit dashboard doesn't show data | Live data log empty | Run `python src/serial_simulator.py` in another terminal or use `--demo` |
| Serial port access denied | Another program (e.g. Arduino Serial Monitor) has locked the COM port | Close Arduino Serial Monitor before starting `serial_reader.py` |
| Bridge rejects packets | Telemetry line does not match the 7-field CSV contract | Run `python validation/protocol_contract_test.py` to inspect syntax |
| Pytest not found | `requirements-dev.txt` not installed in active environment | Run `pip install -r requirements-dev.txt` inside your virtual environment |
