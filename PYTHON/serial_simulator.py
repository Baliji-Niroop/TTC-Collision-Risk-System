"""
Serial Simulator — Simulated ESP32 Telemetry Output
=====================================================
This script emulates the data that a real ESP32 sensor module would produce.
It generates telemetry values (distance, speed, TTC) and writes them to
LOGS/live_data.txt so that the Streamlit dashboard can read and display
them in "Live Log" mode.

How it works:
  - A virtual obstacle starts at 40 metres and the vehicle approaches at
    a constant 15 km/h.
  - On each tick (every 0.3 seconds) the distance is reduced by v * dt.
  - When the distance reaches 0.3 m (near-collision), the obstacle is
    reset back to 40 m, simulating a new approach cycle.
  - Two TTC values are calculated:
      TTC_basic : assumes constant velocity       → d / v
      TTC_ext   : assumes constant deceleration   → solved from kinematics
  - A risk class (0/1/2) is assigned based on TTC thresholds.
  - The line is written to LOGS/live_data.txt (overwritten each tick).

CSV output format (7 fields, comma-separated):
    timestamp_ms, distance_cm, speed_kmh, ttc_basic, ttc_ext, risk, confidence

Usage:
    python serial_simulator.py
    (then in another terminal: streamlit run dashboard.py, select "Live Log")
"""

import time
import math
from pathlib import Path

# ---------------------------------------------------------------------------
# Path Configuration
# ---------------------------------------------------------------------------
# This script lives in PYTHON/, so the project root is one level up.
# The output file is LOGS/live_data.txt, shared with the dashboard.
BASE_DIR  = Path(__file__).resolve().parent
ROOT_DIR  = BASE_DIR.parent
DATA_FILE = ROOT_DIR / "LOGS" / "live_data.txt"

# Ensure the LOGS directory exists before writing
DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Simulation Parameters
# ---------------------------------------------------------------------------
INITIAL_DISTANCE_M = 40.0       # Starting distance to obstacle (metres)
CLOSING_SPEED_KMH  = 15.0       # Constant approach speed (km/h)
DECEL_MS2          = 5.0        # Assumed braking deceleration (m/s^2)
LOOP_DT            = 0.3        # Time step per simulation tick (seconds)


def compute_ttc_extended(dist_m, v_ms, a=5.0):
    """
    Calculate the extended TTC assuming constant deceleration.

    Uses the kinematic equation:  d = v*t + 0.5*a*t^2
    Rearranged as a quadratic in t:  0.5*a*t^2 + v*t - d = 0
    Solution (positive root):  t = (-v + sqrt(v^2 + 2*a*d)) / a

    Returns 99.0 when the discriminant is negative (physically impossible)
    or the velocity is near-zero (no collision expected).
    """
    disc = v_ms * v_ms + 2 * a * dist_m
    if disc < 0 or v_ms <= 0.01:
        return 99.0
    return (-v_ms + math.sqrt(disc)) / a


def classify_risk(ttc):
    """
    Classify collision risk based on TTC value.

    Risk levels:
        0 (SAFE)     : TTC > 3.0 seconds — no immediate danger
        1 (WARNING)  : 1.5 s < TTC <= 3.0 s — approaching danger zone
        2 (CRITICAL) : TTC <= 1.5 seconds — collision imminent
    """
    if ttc > 3.0:
        return 0
    elif ttc > 1.5:
        return 1
    else:
        return 2


if __name__ == "__main__":
    print("Serial simulator running")
    print(f"Output file: {DATA_FILE}")
    print("Press Ctrl+C to stop\n")

    distance_m = INITIAL_DISTANCE_M
    t_ms = 0    # Simulated timestamp in milliseconds

    while True:
        # Convert closing speed from km/h to m/s for physics calculations
        v_ms = CLOSING_SPEED_KMH / 3.6

        # Reduce distance by the amount travelled in one time step
        distance_m -= v_ms * LOOP_DT

        # Near-collision reset: if the vehicle is within 0.3 m of the
        # obstacle, reset the distance to simulate a fresh approach.
        if distance_m <= 0.3:
            distance_m = INITIAL_DISTANCE_M
            print("[Reset] Obstacle repositioned to 40 m")

        distance_cm = distance_m * 100.0
        v_kmh = CLOSING_SPEED_KMH

        # Calculate both TTC variants
        ttc_basic = distance_m / v_ms if v_ms > 0.1 else 99.0
        ttc_ext   = compute_ttc_extended(distance_m, v_ms, DECEL_MS2)

        # Classify risk and compute a synthetic confidence score.
        # Confidence decreases when the two TTC estimates diverge.
        risk = classify_risk(ttc_basic)
        conf = round(1.0 - abs(ttc_basic - ttc_ext) / (ttc_basic + 0.01) * 0.3, 2)
        conf = max(0.5, min(1.0, conf))

        # Build the CSV line and write it to the shared log file
        line = (
            f"{t_ms},{distance_cm:.2f},{v_kmh:.1f},"
            f"{ttc_basic:.2f},{ttc_ext:.2f},{risk},{conf:.2f}"
        )

        with open(DATA_FILE, "w") as f:
            f.write(line)

        # Console output for monitoring
        labels = ["SAFE", "WARNING", "CRITICAL"]
        print(
            f"t={t_ms:6d} ms | dist={distance_cm:6.1f} cm | "
            f"v={v_kmh:.1f} km/h | TTC={ttc_basic:.2f} s | "
            f"{labels[risk]} | conf={conf:.2f}"
        )

        t_ms += int(LOOP_DT * 1000)
        time.sleep(LOOP_DT)