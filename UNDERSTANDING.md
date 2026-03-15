# Understanding the Project

This project is a forward-collision risk prototype built around one main question:

How much time is left before a collision happens if the vehicle keeps approaching at its current closing speed?

That value is called Time-to-Collision, or TTC.

## Core Idea

The system looks at two main inputs:

1. distance to an obstacle
2. closing speed toward that obstacle

From those values, it estimates TTC and classifies the situation into one of three risk zones:

- `SAFE`: more than 3.0 seconds remaining
- `WARNING`: between 1.5 and 3.0 seconds remaining
- `CRITICAL`: 1.5 seconds or less remaining

The lower the TTC, the less reaction time remains.

## How The Project Works

The project is built as a small monitoring pipeline.

1. Telemetry enters the system.
2. The telemetry is validated.
3. TTC and risk are evaluated.
4. The dashboard updates the live display.
5. Logs and session statistics are recorded.

## Telemetry Sources

The current code supports three input paths.

### 1. Simulator mode

This is the easiest mode to run. The dashboard generates synthetic approach data in-process and uses it directly.

Use this when:

- you want a quick demo,
- no hardware is connected,
- you want to test the UI and logic flow.

### 2. Live Log mode

In this mode, the dashboard reads the latest telemetry line from `LOGS/live_data.txt`.

That file can be updated by:

- `serial_simulator.py`, or
- `serial_reader.py`.

This mode acts as a simple bridge between the dashboard and a separate telemetry process.

### 3. ESP32 Serial mode

In this mode, the dashboard or the serial pipeline reads directly from a USB serial connection using `pyserial`.

This is the path intended for real hardware, but it depends on the ESP32 sending data in the expected 7-field format.

## Main Components

### `dashboard.py`

This is the main user-facing application. It:

- collects telemetry from one of the supported sources,
- loads the ML model if available,
- falls back to TTC threshold logic if the model is unavailable,
- displays live metrics, status banners, charts, and session summaries.

### `serial_simulator.py`

This script creates synthetic telemetry for testing. It simulates an approaching obstacle, computes TTC, classifies risk, and writes the latest reading to `LOGS/live_data.txt`.

### `serial_reader.py`

This script is the Python-side receiver for real hardware. It reads serial packets from an ESP32, writes the latest packet to `LOGS/live_data.txt`, and saves the full session as a CSV file when stopped.

### `validators.py`

This module checks that telemetry is structurally valid and physically reasonable. It rejects malformed rows and flags suspicious values.

### `alerts.py`

This module controls alert triggering and throttling so the system can react to warning and critical states without spamming events unnecessarily.

### `analytics.py`

This module stores session events and calculates summaries such as TTC statistics, trend direction, and critical-event counts.

### `safety_features.py`

This module contains extra protection logic, including:

- hysteresis to reduce alert flicker,
- sensor fault detection,
- velocity sanity checking,
- confidence-aware ML and physics fusion helpers.

## TTC Logic In Practice

The project uses TTC as the simplest safety signal.

If the closing speed stays positive and the object ahead keeps getting nearer, TTC drops. When it drops below the configured thresholds, the system moves from `SAFE` to `WARNING` to `CRITICAL`.

The code also calculates two TTC variants:

- a basic constant-speed TTC,
- an extended TTC that considers deceleration assumptions.

These values help the dashboard show not just raw distance, but the urgency of the situation.

## Machine Learning vs. Physics Rules

The system supports both approaches.

- If the trained model loads successfully, the dashboard can use it for risk prediction.
- If the model is missing or incompatible, the project still works by using TTC threshold rules.

This fallback matters because it keeps the dashboard usable even when the ML path is unavailable.

## Why The Project Is Not Finished Yet

The software foundation is largely in place, but the hardware side is still the main gap.

What already exists:

- dashboard
- simulator
- Python serial receiver
- logging and analytics
- validation and safety-support modules

What is still missing:

- actual ESP32 firmware
- real sensor wiring and bring-up
- calibration with physical measurements
- real-world validation and testing

So the project should currently be understood as a strong software prototype waiting for real hardware execution.

## Where To Change Settings

Most system settings live in `PYTHON/config.py`, including:

- TTC thresholds
- serial baud rate and timeout
- simulator parameters
- dashboard refresh rate
- logging options

Changing those values affects system behavior globally.

## What To Read Next

- Read `README.md` for setup and run instructions.
- Read `status.md` for the current maturity of the project.
- Read `SERIAL_PROTOCOL.md` before implementing or changing ESP32 firmware.
- Read `INTEGRATION_STATUS.md` to see what hardware work is still pending.
