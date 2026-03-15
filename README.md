# TTC Collision Risk Monitoring System

This project is a real-time safety system designed to measure collision risk based on distance and speed. It continuously calculates the Time-to-Collision (TTC) to provide immediate feedback on whether the current approach is safe or poses a risk.

## Project Structure

The project is organized efficiently to separate source code, models, and runtime logs:

* **PYTHON/**: Contains all source code modules for the system.
  * `dashboard.py`: The Streamlit web interface for visualizing real-time data.
  * `serial_simulator.py`: A physics-based simulator generating test telemetry.
  * `serial_reader.py`: Interfaces with physical hardware (e.g., ESP32 sensors).
  * `config.py`: Centralized configuration attributes.
  * `validators.py`, `alerts.py`, `analytics.py`, `safety_features.py`, `logger.py`, `utils.py`: Supporting logic and utilities.
* **MODELS/**: Stores the trained Machine Learning models used for advanced risk validation.
* **LOGS/**: Auto-generated directory storing live sensor data and system event logs.

## Getting Started

To run the application locally, you can use the provided batch script or run the components manually.

### One-Click Launch

Simply run the batch file to start both the simulator and the dashboard:
```cmd
run_dashboard.bat
```

### Manual Launch

If you prefer to start the processes individually, open two separate terminals. Ensure your virtual environment (`ttc_env`) is activated in both.

Terminal 1 (Telemetry Simulator):
```cmd
python PYTHON/serial_simulator.py
```

Terminal 2 (Dashboard Interface):
```cmd
streamlit run PYTHON/dashboard.py
```

After starting the dashboard, navigate your browser to `http://localhost:8501`.

## Documentation

For further information regarding the system's logic and current progress, please refer to:
* `understanding.md`: A straightforward explanation of the system's core concepts.
* `status.md`: The current project checklist and development status.
