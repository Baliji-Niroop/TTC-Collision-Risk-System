"""
serial_reader.py
Reads live telemetry from an ESP32 over USB serial.

Does two things:
  1. Writes the latest reading to LOGS/live_data.txt for the dashboard.
  2. Saves the full session as a timestamped CSV when stopped (Ctrl+C).

Expected format: 7 comma-separated fields per line
    timestamp_ms, distance_cm, speed_kmh, ttc_basic, ttc_ext, risk_class, confidence

Usage:
    python serial_reader.py                  # auto-detect port
    python serial_reader.py --port COM3      # specify port
    python serial_reader.py --list           # list available ports
"""

# Imports
import serial
import serial.tools.list_ports
import pandas as pd
import argparse
import datetime
import sys
from pathlib import Path

# Try to import project modules for enhanced logging and validation
try:
    from config import SERIAL_CONFIG, LOG_DIR
    from logger import get_logger
    from validators import validate_csv_line
    from telemetry_schema import format_packet
    logger = get_logger(__name__)
except ImportError:
    logger = None
    LOG_DIR = None
    SERIAL_CONFIG = {"baud_rate": 115200, "timeout": 2}
    validate_csv_line = None
    format_packet = None

# Column names for the session CSV export
COLUMNS = [
    "timestamp_ms",
    "distance_cm",
    "speed_kmh",
    "ttc_basic",
    "ttc_ext",
    "risk_class",
    "confidence",
]

RISK_LABELS = {0: "SAFE", 1: "WARNING", 2: "CRITICAL"}

# Constants for file paths and communication
BAUD_RATE = SERIAL_CONFIG.get("baud_rate", 115200)
LOG_FILE_TPL = "session_{}.csv"  # Template for timestamped session files
if LOG_DIR:
    LIVE_FILE = LOG_DIR / "live_data.txt"
else:
    LOG_DIR = Path(__file__).parent.parent / "LOGS"
    LIVE_FILE = Path(__file__).parent.parent / "LOGS" / "live_data.txt"


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
            if logger:
                logger.error("No serial ports available")
            sys.exit(1)
        args.port = ports[0]
        print(f"Auto-selected port: {args.port}")
        if logger:
            logger.info(f"Auto-selected port: {args.port}")

    # Generate a unique session filename using the current timestamp
    session_ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / LOG_FILE_TPL.format(session_ts)
    session_data = []       # Accumulates all parsed rows for the session CSV

    print(f"\nConnecting to {args.port} at {args.baud} baud ...")
    if logger:
        logger.info(f"Connecting to {args.port} at {args.baud} baud")

    # Attempt to open the serial port
    try:
        ser = serial.Serial(args.port, args.baud, timeout=SERIAL_CONFIG.get("timeout", 2))
        if logger:
            logger.info(f"Serial connection opened successfully")
    except serial.SerialException as e:
        print(f"ERROR: Could not open serial port — {e}")
        if logger:
            logger.error(f"Failed to open serial port: {e}")
        sys.exit(1)

    print(f"Connected. Session log: {log_file.name}")
    print("Press Ctrl+C to stop.\n")
    if logger:
        logger.info(f"Serial reader started. Session log: {log_file.name}")

    try:
        while True:
            # Read one line from the serial buffer (blocks until newline or timeout)
            try:
                raw = ser.readline()
            except serial.SerialException as e:
                if logger:
                    logger.error(f"Serial read error: {e}")
                print(f"Serial read error: {e}")
                continue
                
            if not raw:
                continue

            # Decode bytes to string, ignoring any malformed characters
            try:
                line = raw.decode(SERIAL_CONFIG.get("encoding", "utf-8"), errors="ignore").strip()
            except Exception as e:
                if logger:
                    logger.warning(f"Decode error: {e}")
                continue

            if not line:
                continue

            # The ESP32 sends 7 comma-separated values per line.
            # Lines with a different number of fields are skipped.
            parts = line.split(",")
            if len(parts) != SERIAL_CONFIG.get("expected_fields", 7):
                if logger:
                    logger.debug(f"Invalid field count: {len(parts)}")
                continue

            # Parse each field into its expected numeric type
            try:
                row = validate_csv_line(line) if validate_csv_line else None
            except (ValueError, IndexError) as e:
                if logger:
                    logger.debug(f"Parse error: {e}")
                continue

            if row is None:
                continue

            session_data.append(row)

            # Write the normalized canonical packet to the shared live data file so the
            # Streamlit dashboard sees the same frozen schema every time.
            try:
                with open(LIVE_FILE, "w", encoding="utf-8") as f:
                    f.write(format_packet(row) + "\n" if format_packet else line + "\n")
            except IOError as e:
                if logger:
                    logger.error(f"Failed to write live data file: {e}")

            # Pretty-print each reading to the console for monitoring
            output = (
                f"{row['timestamp_ms']:>8.0f} ms | "
                f"{row['distance_cm']:>6.1f} cm | "
                f"{row['speed_kmh']:>5.1f} km/h | "
                f"TTC={row['ttc_basic']:>5.2f}s | "
                f"{RISK_LABELS.get(row['risk_class'], '?')} | "
                f"conf={row['confidence']:.2f}"
            )
            print(output)

    except KeyboardInterrupt:
        print("\nStopping ...")
        if logger:
            logger.info("Serial reader stopped by user")

    except Exception as e:
        print(f"Unexpected error: {e}")
        if logger:
            logger.error(f"Unexpected error: {e}")

    finally:
        ser.close()
        if logger:
            logger.info("Serial connection closed")

        # Save the full session to a CSV file for later analysis
        if session_data:
            try:
                df = pd.DataFrame(session_data, columns=COLUMNS)
                df.to_csv(log_file, index=False)
                print(f"\nSaved {len(session_data)} rows to {log_file}")
                print(f"Min TTC: {df['ttc_basic'].min():.2f} s")
                print(f"CRITICAL events: {(df['risk_class'] == 2).sum()}")
                if logger:
                    logger.info(f"Session saved: {len(session_data)} rows to {log_file}")
            except Exception as e:
                print(f"Error saving session: {e}")
                if logger:
                    logger.error(f"Error saving session: {e}")
        else:
            print("No data was recorded during this session.")
            if logger:
                logger.warning("No data recorded in session")


if __name__ == "__main__":
    main()