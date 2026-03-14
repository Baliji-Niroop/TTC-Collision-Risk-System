"""
serial_simulator.py
Simulates ESP32 serial output for dashboard testing.
Writes data into LOGS/live_data.txt (project structure compatible).
"""

import time
import math
from pathlib import Path

# ───────── PATH FIX (IMPORTANT) ─────────
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
DATA_FILE = ROOT_DIR / "LOGS" / "live_data.txt"

# ───────── Simulation parameters ─────────
INITIAL_DISTANCE_M = 40.0
CLOSING_SPEED_KMH  = 15.0
DECEL_MS2          = 5.0
LOOP_DT            = 0.3

def compute_ttc_extended(dist_m, v_ms, a=5.0):
    disc = v_ms*v_ms + 2*a*dist_m
    if disc < 0 or v_ms <= 0.01:
        return 99.0
    return (-v_ms + math.sqrt(disc)) / a

def classify_risk(ttc):
    if ttc > 3.0:
        return 0
    elif ttc > 1.5:
        return 1
    else:
        return 2

if __name__ == "__main__":
    print("✅ Serial simulator running")
    print(f"Writing data to: {DATA_FILE}")
    print("Press Ctrl+C to stop\n")

    distance_m = INITIAL_DISTANCE_M
    t_ms = 0

    while True:

        v_ms = CLOSING_SPEED_KMH / 3.6
        distance_m -= v_ms * LOOP_DT

        if distance_m <= 0.3:
            distance_m = INITIAL_DISTANCE_M
            print("🔁 Reset obstacle to 40 m")

        distance_cm = distance_m * 100.0
        v_kmh = CLOSING_SPEED_KMH

        ttc_basic = distance_m / v_ms if v_ms > 0.1 else 99.0
        ttc_ext   = compute_ttc_extended(distance_m, v_ms, DECEL_MS2)

        risk = classify_risk(ttc_basic)

        conf = round(1.0 - abs(ttc_basic - ttc_ext)/(ttc_basic+0.01)*0.3, 2)
        conf = max(0.5, min(1.0, conf))

        line = f"{t_ms},{distance_cm:.2f},{v_kmh:.1f},{ttc_basic:.2f},{ttc_ext:.2f},{risk},{conf:.2f}"

        # ─── WRITE FILE ───
        with open(DATA_FILE, "w") as f:
            f.write(line)

        labels = ["SAFE", "WARNING", "CRITICAL"]

        print(
            f"t={t_ms:6d} ms | dist={distance_cm:6.1f} cm | "
            f"v={v_kmh:.1f} km/h | TTC={ttc_basic:.2f} s | "
            f"{labels[risk]} | conf={conf:.2f}"
        )

        t_ms += int(LOOP_DT * 1000)
        time.sleep(LOOP_DT)