"""
serial_reader.py
Reads live data from ESP32 serial port and logs to CSV.
Compatible with new project folder structure.
"""

import serial
import serial.tools.list_ports
import pandas as pd
import argparse
import datetime
import sys
from pathlib import Path

BAUD_RATE = 115200

# ───── PATH FIX ─────
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
LOG_DIR  = ROOT_DIR / "LOGS"

LIVE_FILE    = LOG_DIR / "live_data.txt"
LOG_FILE_TPL = LOG_DIR / "session_{}.csv"

COLUMNS = [
    "timestamp_ms","distance_cm","v_closing_kmh",
    "ttc_basic_s","ttc_ext_s","risk_class","confidence"
]

RISK_LABELS = {0: "SAFE", 1: "WARNING", 2: "CRITICAL"}


def list_ports():
    ports = serial.tools.list_ports.comports()
    if not ports:
        print("No serial ports detected.")
    else:
        print("Available ports:")
        for p in ports:
            print(f"  {p.device}  –  {p.description}")


def main():

    parser = argparse.ArgumentParser(description="TTC Serial Reader")
    parser.add_argument("--port", default=None)
    parser.add_argument("--baud", type=int, default=BAUD_RATE)
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()

    if args.list:
        list_ports()
        sys.exit(0)

    if args.port is None:
        ports = [p.device for p in serial.tools.list_ports.comports()]
        if not ports:
            print("ERROR: No serial port detected.")
            list_ports()
            sys.exit(1)
        args.port = ports[0]
        print(f"Auto-selected port: {args.port}")

    session_ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_FILE_TPL.format(session_ts)
    session_data = []

    print(f"\nConnecting to {args.port} @ {args.baud} baud …")

    try:
        ser = serial.Serial(args.port, args.baud, timeout=2)
    except serial.SerialException as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    print(f"Connected. Logging to {log_file.name}")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:

            raw = ser.readline()
            if not raw:
                continue

            try:
                line = raw.decode("utf-8", errors="ignore").strip()
            except Exception:
                continue

            if not line:
                continue

            parts = line.split(",")
            if len(parts) != 7:
                continue

            try:
                row = [
                    float(parts[0]),
                    float(parts[1]),
                    float(parts[2]),
                    float(parts[3]),
                    float(parts[4]),
                    int(parts[5]),
                    float(parts[6]),
                ]
            except:
                continue

            session_data.append(row)

            # ───── WRITE FOR DASHBOARD ─────
            with open(LIVE_FILE, "w") as f:
                f.write(line)

            risk_label = RISK_LABELS.get(row[5], "?")

            print(
                f"{row[0]:>8.0f} ms | "
                f"{row[1]:>6.1f} cm | "
                f"{row[2]:>5.1f} km/h | "
                f"TTC={row[3]:>5.2f}s | "
                f"{risk_label} | "
                f"conf={row[6]:.2f}"
            )

    except KeyboardInterrupt:
        print("\nStopping…")

    finally:
        ser.close()

        if session_data:
            df = pd.DataFrame(session_data, columns=COLUMNS)
            df.to_csv(log_file, index=False)

            print(f"\nSaved {len(session_data)} rows → {log_file}")
            print(f"Min TTC: {df['ttc_basic_s'].min():.2f}s")
            print(f"CRITICAL events: {(df['risk_class']==2).sum()}")
        else:
            print("No data recorded.")


if __name__ == "__main__":
    main()