"""
Serial Reader — ESP32 Live Data Acquisition
=============================================
This script reads real-time telemetry data from an ESP32 (or compatible
microcontroller) over a USB serial connection and performs two tasks:

  1. Writes the latest reading to LOGS/live_data.txt so that the Streamlit
     dashboard can display it in "Live Log" mode.
  2. Accumulates every reading in memory and saves the full session as a
     timestamped CSV file in LOGS/ when the script is stopped (Ctrl+C).

Expected serial format (7 comma-separated fields per line):
    timestamp_ms, distance_cm, speed_kmh, ttc_basic, ttc_ext, risk_class, confidence

Command-line usage:
    python serial_reader.py                    # Auto-detect first available port
    python serial_reader.py --port COM3        # Specify a port explicitly
    python serial_reader.py --list             # List all available serial ports
    python serial_reader.py --baud 9600        # Override baud rate (default 115200)
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------
import serial
import serial.tools.list_ports
import pandas as pd
import argparse
import datetime
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BAUD_RATE = 115200      # Default baud rate — must match ESP32 firmware

# Path setup: this script is in PYTHON/, so the project root is one level up.
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
LOG_DIR  = ROOT_DIR / "LOGS"

# LIVE_FILE is overwritten each tick so the dashboard always reads the latest.
# LOG_FILE_TPL is used to generate a unique session CSV filename on exit.
LIVE_FILE    = LOG_DIR / "live_data.txt"
LOG_FILE_TPL = LOG_DIR / "session_{}.csv"

# Column names for the session CSV export
COLUMNS = [
    "timestamp_ms",
    "distance_cm",
    "v_closing_kmh",
    "ttc_basic_s",
    "ttc_ext_s",
    "risk_class",
    "confidence",
]

RISK_LABELS = {0: "SAFE", 1: "WARNING", 2: "CRITICAL"}


def list_ports():
    """Print all serial ports detected on this machine."""
    ports = serial.tools.list_ports.comports()
    if not ports:
        print("No serial ports detected.")
    else:
        print("Available serial ports:")
        for p in ports:
            print(f"  {p.device}  —  {p.description}")


def main():
    """
    Main entry point.

    1. Parse command-line arguments (--port, --baud, --list).
    2. Open the serial connection.
    3. Enter a read loop: parse each line, display in the console, write to
       the live data file, and accumulate in memory.
    4. On Ctrl+C, close the port and save the full session to a CSV file.
    """
    parser = argparse.ArgumentParser(
        description="TTC Serial Reader — reads live telemetry from ESP32"
    )
    parser.add_argument("--port", default=None,
                        help="Serial port (e.g. COM3). Auto-detected if omitted.")
    parser.add_argument("--baud", type=int, default=BAUD_RATE,
                        help=f"Baud rate (default: {BAUD_RATE})")
    parser.add_argument("--list", action="store_true",
                        help="List available serial ports and exit")
    args = parser.parse_args()

    # If --list is passed, just show available ports and exit
    if args.list:
        list_ports()
        sys.exit(0)

    # Auto-detect the first available serial port if none was specified
    if args.port is None:
        ports = [p.device for p in serial.tools.list_ports.comports()]
        if not ports:
            print("ERROR: No serial port detected.")
            list_ports()
            sys.exit(1)
        args.port = ports[0]
        print(f"Auto-selected port: {args.port}")

    # Generate a unique session filename using the current timestamp
    session_ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_FILE_TPL.format(session_ts)
    session_data = []       # Accumulates all parsed rows for the session CSV

    print(f"\nConnecting to {args.port} at {args.baud} baud ...")

    # Attempt to open the serial port
    try:
        ser = serial.Serial(args.port, args.baud, timeout=2)
    except serial.SerialException as e:
        print(f"ERROR: Could not open serial port — {e}")
        sys.exit(1)

    print(f"Connected. Session log: {log_file.name}")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            # Read one line from the serial buffer (blocks until newline or timeout)
            raw = ser.readline()
            if not raw:
                continue

            # Decode bytes to string, ignoring any malformed characters
            try:
                line = raw.decode("utf-8", errors="ignore").strip()
            except Exception:
                continue

            if not line:
                continue

            # The ESP32 sends 7 comma-separated values per line.
            # Lines with a different number of fields are skipped.
            parts = line.split(",")
            if len(parts) != 7:
                continue

            # Parse each field into its expected numeric type
            try:
                row = [
                    float(parts[0]),    # timestamp_ms
                    float(parts[1]),    # distance_cm
                    float(parts[2]),    # v_closing_kmh
                    float(parts[3]),    # ttc_basic_s
                    float(parts[4]),    # ttc_ext_s
                    int(parts[5]),      # risk_class (0, 1, or 2)
                    float(parts[6]),    # confidence (0.0 to 1.0)
                ]
            except (ValueError, IndexError):
                continue

            session_data.append(row)

            # Write the raw CSV line to the shared live data file so the
            # Streamlit dashboard can pick it up on its next refresh cycle.
            with open(LIVE_FILE, "w") as f:
                f.write(line)

            # Pretty-print each reading to the console for monitoring
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
        print("\nStopping ...")

    finally:
        ser.close()

        # Save the full session to a CSV file for later analysis
        if session_data:
            df = pd.DataFrame(session_data, columns=COLUMNS)
            df.to_csv(log_file, index=False)
            print(f"\nSaved {len(session_data)} rows to {log_file}")
            print(f"Min TTC: {df['ttc_basic_s'].min():.2f} s")
            print(f"CRITICAL events: {(df['risk_class'] == 2).sum()}")
        else:
            print("No data was recorded during this session.")


if __name__ == "__main__":
    main()