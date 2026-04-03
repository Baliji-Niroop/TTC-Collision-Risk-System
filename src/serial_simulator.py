"""
serial_simulator.py
Generates synthetic TTC telemetry and writes it to LOGS/live_data.txt.

Simulates a vehicle approaching an obstacle at 15 km/h, starting from 40m.
When distance drops to 0.3m (near-collision), the obstacle resets to 40m.
The dashboard can read this file in Live Log mode.

Output format (7 CSV fields per line):
    timestamp_ms, distance_cm, speed_kmh, ttc_basic, ttc_ext, risk_class, confidence

Usage:  python serial_simulator.py
"""

import time
import math
from pathlib import Path

# Try to import project modules for enhanced logging
try:
    from config import (
        ROOT_DIR, SIMULATOR_CONFIG, get_risk_class
    )
    from logger import get_logger
    from telemetry_schema import canonical_row, format_packet
    logger = get_logger(__name__)
    DATA_FILE = ROOT_DIR / "LOGS" / "live_data.txt"
    INITIAL_DISTANCE_M = SIMULATOR_CONFIG.get("initial_distance_m", 40.0)
    CLOSING_SPEED_KMH = SIMULATOR_CONFIG.get("closing_speed_kmh", 15.0)
    DECEL_MS2 = SIMULATOR_CONFIG.get("deceleration_ms2", 5.0)
    LOOP_DT = SIMULATOR_CONFIG.get("loop_dt", 0.3)
except ImportError:
    logger = None
    BASE_DIR = Path(__file__).resolve().parent
    ROOT_DIR = BASE_DIR.parent
    DATA_FILE = ROOT_DIR / "LOGS" / "live_data.txt"
    INITIAL_DISTANCE_M = 40.0
    CLOSING_SPEED_KMH = 15.0
    DECEL_MS2 = 5.0
    LOOP_DT = 0.3
    get_risk_class = None

    def canonical_row(*args, **kwargs):
        return {
            "timestamp_ms": float(args[0]),
            "distance_cm": float(args[1]),
            "speed_kmh": float(args[2]),
            "ttc_basic": float(args[3]),
            "ttc_ext": float(args[4]),
            "risk_class": int(args[5]),
            "confidence": float(args[6]),
        }

    def format_packet(row):
        return (
            f"{int(round(row['timestamp_ms']))},"
            f"{row['distance_cm']:.2f},"
            f"{row['speed_kmh']:.2f},"
            f"{row['ttc_basic']:.2f},"
            f"{row['ttc_ext']:.2f},"
            f"{int(row['risk_class'])},"
            f"{row['confidence']:.2f}"
        )


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
    if get_risk_class:
        return get_risk_class(ttc)
    
    # Fallback logic if config module not imported
    if ttc > 3.0:
        return 0
    elif ttc > 1.5:
        return 1
    else:
        return 2


if __name__ == "__main__":
    # Ensure LOGS directory exists
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    print("Serial simulator running")
    print(f"Output file: {DATA_FILE}")
    print("Press Ctrl+C to stop\n")
    
    if logger:
        logger.info("Serial simulator started")
        logger.info(f"Output file: {DATA_FILE}")
        logger.info(f"Config: Initial distance={INITIAL_DISTANCE_M}m, Speed={CLOSING_SPEED_KMH} km/h")

    distance_m = INITIAL_DISTANCE_M
    t_ms = 0    # Simulated timestamp in milliseconds

    try:
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
                if logger:
                    logger.info("Obstacle reset")

            distance_cm = distance_m * 100.0
            v_kmh = CLOSING_SPEED_KMH

            # Calculate both TTC variants
            ttc_basic = distance_m / v_ms if v_ms > 0.1 else 99.0
            ttc_ext   = compute_ttc_extended(distance_m, v_ms, DECEL_MS2)

            # Classify risk and compute a synthetic confidence score.
            # Confidence decreases when the two TTC estimates diverge.
            risk_class = classify_risk(ttc_basic)
            conf = round(1.0 - abs(ttc_basic - ttc_ext) / (ttc_basic + 0.01) * 0.3, 2)
            conf = max(0.5, min(1.0, conf))

            packet = canonical_row(t_ms, distance_cm, v_kmh, ttc_basic, ttc_ext, risk_class, conf)
            line = format_packet(packet)

            try:
                # Atomic write: write to temp file then rename to avoid
                # dashboard reading a half-written line (race condition).
                tmp_file = DATA_FILE.with_suffix(".tmp")
                with open(tmp_file, "w", encoding="utf-8") as f:
                    f.write(line)
                tmp_file.replace(DATA_FILE)
            except IOError as e:
                print(f"Error writing to {DATA_FILE}: {e}")
                if logger:
                    logger.error(f"Failed to write data file: {e}")

            # Console output for monitoring
            labels = ["SAFE", "WARNING", "CRITICAL"]
            output = (
                f"t={t_ms:6d} ms | dist={distance_cm:6.1f} cm | "
                f"v={v_kmh:.1f} km/h | TTC={ttc_basic:.2f} s | "
                f"{labels[risk_class]} | conf={conf:.2f}"
            )
            print(output)

            t_ms += int(LOOP_DT * 1000)
            time.sleep(LOOP_DT)
    
    except KeyboardInterrupt:
        print("\nSimulator stopped.")
        if logger:
            logger.info("Serial simulator stopped by user")
    
    except Exception as e:
        print(f"Error in simulator: {e}")
        if logger:
            logger.error(f"Simulator error: {e}")