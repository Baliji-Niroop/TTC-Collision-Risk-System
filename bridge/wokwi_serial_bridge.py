"""
Wokwi serial bridge for Windows.

Reads canonical telemetry from either a websocket stream or stdin, validates
each packet with the strict Python parser, and forwards valid rows to:
  - a virtual COM port for serial_reader.py, and/or
  - LOGS/live_data.txt for dashboard Live Log mode.

The bridge can also launch the serial_reader and dashboard as child processes
when run in stack mode.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Iterable, Optional

try:
    import serial
except ImportError:  # pragma: no cover - handled at runtime
    serial = None

try:
    import websocket
except ImportError:  # pragma: no cover - handled at runtime
    websocket = None

# Create fallback exception class if serial is not available
if serial is None:

    class SerialException(Exception):
        """Fallback exception when pyserial is not installed."""

        pass

else:
    SerialException = serial.SerialException

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
VALIDATION_DIR = ROOT_DIR / "validation"
LOG_DIR = ROOT_DIR / "LOGS"
LIVE_FILE = LOG_DIR / "live_data.txt"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from validators import validate_csv_line  # noqa: E402
from telemetry_schema import format_packet  # noqa: E402
from logger import get_logger  # noqa: E402

logger = get_logger(__name__)

CANONICAL_FIELDS = (
    "timestamp_ms,distance_cm,speed_kmh,ttc_basic,ttc_ext,risk_class,confidence"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Wokwi serial bridge for the TTC project"
    )
    parser.add_argument(
        "--source", choices=["auto", "websocket", "stdin"], default="auto"
    )
    parser.add_argument("--ws-url", default=os.environ.get("WOKWI_SERIAL_WS_URL"))
    parser.add_argument(
        "--serial-out", default=os.environ.get("WOKWI_BRIDGE_SERIAL_OUT")
    )
    parser.add_argument("--launch-stack", action="store_true", default=True)
    parser.add_argument("--no-launch-stack", dest="launch_stack", action="store_false")
    parser.add_argument("--reader-port", default=os.environ.get("WOKWI_READER_PORT"))
    parser.add_argument(
        "--dashboard-port", default=os.environ.get("TTC_DASHBOARD_PORT", "8501")
    )
    parser.add_argument(
        "--dashboard-mode",
        default=os.environ.get("TTC_DASHBOARD_DEFAULT_MODE", "Live Log"),
    )
    parser.add_argument(
        "--validation-test", default=str(VALIDATION_DIR / "protocol_contract_test.py")
    )
    return parser.parse_args()


def run_protocol_preflight(test_path: Path) -> None:
    python_exe = sys.executable
    logger.info("Running protocol preflight: %s", test_path)
    result = subprocess.run(
        [python_exe, str(test_path)], cwd=str(ROOT_DIR), capture_output=True, text=True
    )
    if result.returncode != 0:
        logger.error(
            "Protocol contract test failed:\n%s\n%s", result.stdout, result.stderr
        )
        raise SystemExit(result.returncode)
    logger.info("Protocol preflight passed")


def open_serial_port(port_name: str):
    """
    Open a virtual COM port for forwarding telemetry.

    Args:
        port_name: COM port identifier (e.g., 'COM3')

    Returns:
        serial.Serial object or None if port fails to open

    Raises:
        RuntimeError: If pyserial is not installed
    """
    if serial is None:
        raise RuntimeError("pyserial is not installed")

    try:
        port = serial.Serial(port_name, 115200, timeout=1)
        logger.info("Successfully opened serial port: %s", port_name)
        return port
    except serial.SerialException as e:
        logger.error("Failed to open serial port %s: %s", port_name, e)
        logger.warning("Continuing without COM port forwarding")
        return None


def write_live_file(line: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LIVE_FILE.write_text(line.strip() + "\n", encoding="utf-8")


def forward_packet(line: str, serial_port) -> bool:
    """
    Validate, normalize, and forward a telemetry packet.

    Packet flow:
      1. Parse and validate CSV fields
      2. Apply telemetry schema (field order, types, precision)
      3. Forward to serial port (if available)
      4. Write to live_data.txt for dashboard

    Args:
        line: Raw telemetry string from Wokwi
        serial_port: Optional serial.Serial object

    Returns:
        True if packet was successfully forwarded, False otherwise
    """
    valid_row = validate_csv_line(line)
    if valid_row is None:
        logger.error("Rejected malformed packet: %s", line)
        return False

    try:
        normalized = format_packet(valid_row) + "\n"
    except (ValueError, TypeError) as e:
        logger.error("Failed to format packet: %s (error: %s)", line, e)
        return False

    # Attempt serial forwarding
    if serial_port is not None:
        try:
            serial_port.write(normalized.encode("utf-8"))
            serial_port.flush()
        except (SerialException, OSError) as e:
            logger.warning("Failed to write to serial port: %s", e)
            logger.warning("Packet will be written to live_data.txt only")

    # Always write to live_data.txt for dashboard
    try:
        write_live_file(normalized)
    except (IOError, OSError) as e:
        logger.error("Failed to write live_data.txt: %s", e)
        return False

    logger.info("Forwarded canonical packet: %s", normalized.strip())
    return True


def websocket_lines(ws_url: str) -> Iterable[str]:
    """
    Stream telemetry lines from Wokwi websocket with automatic reconnection.

    Handles:
      - Initial connection failures
      - Mid-stream disconnections
      - Exponential backoff (1s → 10s) between retries
      - Graceful shutdown on KeyboardInterrupt

    Args:
        ws_url: Wokwi websocket URL (e.g., ws://localhost:8765)

    Yields:
        Telemetry lines from the simulator

    Raises:
        KeyboardInterrupt: When user terminates
    """
    if websocket is None:
        raise RuntimeError(
            "websocket-client is not installed. Install with: pip install websocket-client"
        )

    retry_delay = 1.0
    max_retry_delay = 10.0

    while True:
        try:
            logger.info("Connecting to Wokwi websocket: %s", ws_url)
            socket = websocket.create_connection(ws_url, timeout=10)
            retry_delay = 1.0
            logger.info("Websocket connected successfully")

            while True:
                try:
                    message = socket.recv()
                    if message is None:
                        logger.warning("Websocket received None, reconnecting...")
                        break

                    if isinstance(message, bytes):
                        message = message.decode("utf-8", errors="ignore")

                    for raw_line in str(message).splitlines():
                        if raw_line.strip():
                            yield raw_line.strip()

                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    logger.error("Error reading from websocket: %s", e)
                    break

        except KeyboardInterrupt:
            raise
        except Exception as exc:
            logger.warning(
                "Wokwi websocket disconnected: %s (retry in %.1fs)", exc, retry_delay
            )
            time.sleep(retry_delay)
            retry_delay = min(retry_delay * 2.0, max_retry_delay)


def stdin_lines() -> Iterable[str]:
    logger.info("Reading Wokwi serial stream from stdin")
    for raw_line in sys.stdin:
        raw_line = raw_line.strip()
        if raw_line:
            yield raw_line


def launch_child_processes(
    reader_port: Optional[str], dashboard_port: str, dashboard_mode: str
) -> list[subprocess.Popen]:
    processes: list[subprocess.Popen] = []
    python_exe = sys.executable

    if reader_port:
        reader_cmd = [
            python_exe,
            str(SRC_DIR / "serial_reader.py"),
            "--port",
            reader_port,
        ]
        processes.append(subprocess.Popen(reader_cmd, cwd=str(ROOT_DIR)))
        logger.info("Started serial_reader.py on %s", reader_port)

    dashboard_env = os.environ.copy()
    dashboard_env["TTC_DASHBOARD_DEFAULT_MODE"] = dashboard_mode
    dashboard_cmd = [
        python_exe,
        "-m",
        "streamlit",
        "run",
        str(SRC_DIR / "dashboard.py"),
        "--server.headless",
        "true",
        "--server.port",
        dashboard_port,
    ]
    processes.append(
        subprocess.Popen(dashboard_cmd, cwd=str(ROOT_DIR), env=dashboard_env)
    )
    logger.info("Started dashboard on port %s", dashboard_port)

    return processes


def main() -> int:
    """
    Main bridge controller.

    Orchestrates:
      1. Protocol validation preflight
      2. Serial port initialization (with graceful degradation)
      3. Child process launch (reader, dashboard)
      4. Telemetry ingestion loop
      5. Graceful shutdown

    Returns:
        0 on success, non-zero exit code on fatal error
    """
    args = parse_args()

    run_protocol_preflight(Path(args.validation_test))

    serial_port = None
    if args.serial_out:
        serial_port = open_serial_port(args.serial_out)
        if serial_port:
            logger.info("Forwarding canonical packets to COM port %s", args.serial_out)
        else:
            logger.info(
                "Serial port unavailable - packets will be written to live_data.txt only"
            )

    children: list[subprocess.Popen] = []
    if args.launch_stack:
        try:
            children = launch_child_processes(
                args.reader_port, args.dashboard_port, args.dashboard_mode
            )
        except Exception as e:
            logger.error("Failed to launch child processes: %s", e)
            if serial_port:
                serial_port.close()
            return 1

    source_mode = args.source
    if source_mode == "auto":
        source_mode = "websocket" if args.ws_url else "stdin"

    try:
        if source_mode == "websocket":
            if not args.ws_url:
                raise SystemExit(
                    "--ws-url or WOKWI_SERIAL_WS_URL is required for websocket mode"
                )
            line_iterable = websocket_lines(args.ws_url)
        else:
            line_iterable = stdin_lines()

        packet_count = 0
        error_count = 0

        for line in line_iterable:
            if forward_packet(line, serial_port):
                packet_count += 1
            else:
                error_count += 1

            # Log stats periodically
            if packet_count % 100 == 0 and packet_count > 0:
                logger.info(
                    "Bridge stats: %d packets forwarded, %d errors",
                    packet_count,
                    error_count,
                )

    except KeyboardInterrupt:
        logger.info("Bridge interrupted by user")
    except Exception as e:
        logger.error("Unexpected error in main loop: %s", e)
        error_count += 1
    finally:
        if serial_port is not None:
            try:
                serial_port.close()
            except Exception as e:
                logger.warning("Error closing serial port: %s", e)

        for process in children:
            if process.poll() is None:
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning(
                        "Child process did not terminate gracefully, killing..."
                    )
                    process.kill()
                except Exception as e:
                    logger.warning("Error terminating child process: %s", e)

        logger.info(
            "Bridge shutdown complete (forwarded %d packets, %d errors)",
            packet_count,
            error_count,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
