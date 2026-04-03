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
import json
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

CANONICAL_FIELDS = "timestamp_ms,distance_cm,speed_kmh,ttc_basic,ttc_ext,risk_class,confidence"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Wokwi serial bridge for the TTC project")
    parser.add_argument("--source", choices=["auto", "websocket", "stdin"], default="auto")
    parser.add_argument("--ws-url", default=os.environ.get("WOKWI_SERIAL_WS_URL"))
    parser.add_argument("--serial-out", default=os.environ.get("WOKWI_BRIDGE_SERIAL_OUT"))
    parser.add_argument("--launch-stack", action="store_true", default=True)
    parser.add_argument("--no-launch-stack", dest="launch_stack", action="store_false")
    parser.add_argument("--reader-port", default=os.environ.get("WOKWI_READER_PORT"))
    parser.add_argument("--dashboard-port", default=os.environ.get("TTC_DASHBOARD_PORT", "8501"))
    parser.add_argument("--dashboard-mode", default=os.environ.get("TTC_DASHBOARD_DEFAULT_MODE", "Live Log"))
    parser.add_argument("--validation-test", default=str(VALIDATION_DIR / "protocol_contract_test.py"))
    return parser.parse_args()


def run_protocol_preflight(test_path: Path) -> None:
    python_exe = sys.executable
    logger.info("Running protocol preflight: %s", test_path)
    result = subprocess.run([python_exe, str(test_path)], cwd=str(ROOT_DIR), capture_output=True, text=True)
    if result.returncode != 0:
        logger.error("Protocol contract test failed:\n%s\n%s", result.stdout, result.stderr)
        raise SystemExit(result.returncode)
    logger.info("Protocol preflight passed")


def open_serial_port(port_name: str):
    if serial is None:
        raise RuntimeError("pyserial is not installed")
    return serial.Serial(port_name, 115200, timeout=1)


def write_live_file(line: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LIVE_FILE.write_text(line.strip() + "\n", encoding="utf-8")


def forward_packet(line: str, serial_port) -> None:
    valid_row = validate_csv_line(line)
    if valid_row is None:
        logger.error("Rejected malformed packet: %s", line)
        return

    normalized = format_packet(valid_row) + "\n"

    if serial_port is not None:
        serial_port.write(normalized.encode("utf-8"))
        serial_port.flush()

    write_live_file(normalized)
    logger.info("Forwarded canonical packet: %s", normalized.strip())


def websocket_lines(ws_url: str) -> Iterable[str]:
    if websocket is None:
        raise RuntimeError("websocket-client is not installed")

    retry_delay = 1.0
    while True:
        try:
            logger.info("Connecting to Wokwi websocket: %s", ws_url)
            socket = websocket.create_connection(ws_url, timeout=10)
            retry_delay = 1.0
            while True:
                message = socket.recv()
                if message is None:
                    break
                if isinstance(message, bytes):
                    message = message.decode("utf-8", errors="ignore")
                for raw_line in str(message).splitlines():
                    if raw_line.strip():
                        yield raw_line.strip()
        except KeyboardInterrupt:
            raise
        except Exception as exc:
            logger.warning("Wokwi websocket disconnected: %s", exc)
            time.sleep(retry_delay)
            retry_delay = min(retry_delay * 2.0, 10.0)


def stdin_lines() -> Iterable[str]:
    logger.info("Reading Wokwi serial stream from stdin")
    for raw_line in sys.stdin:
        raw_line = raw_line.strip()
        if raw_line:
            yield raw_line


def launch_child_processes(reader_port: Optional[str], dashboard_port: str, dashboard_mode: str) -> list[subprocess.Popen]:
    processes: list[subprocess.Popen] = []
    python_exe = sys.executable

    if reader_port:
        reader_cmd = [python_exe, str(SRC_DIR / "serial_reader.py"), "--port", reader_port]
        processes.append(subprocess.Popen(reader_cmd, cwd=str(ROOT_DIR)))
        logger.info("Started serial_reader.py on %s", reader_port)

    dashboard_env = os.environ.copy()
    dashboard_env["TTC_DASHBOARD_DEFAULT_MODE"] = dashboard_mode
    dashboard_cmd = [python_exe, "-m", "streamlit", "run", str(SRC_DIR / "dashboard.py"), "--server.headless", "true", "--server.port", dashboard_port]
    processes.append(subprocess.Popen(dashboard_cmd, cwd=str(ROOT_DIR), env=dashboard_env))
    logger.info("Started dashboard on port %s", dashboard_port)

    return processes


def main() -> int:
    args = parse_args()

    run_protocol_preflight(Path(args.validation_test))

    serial_port = None
    if args.serial_out:
        serial_port = open_serial_port(args.serial_out)
        logger.info("Forwarding canonical packets to COM port %s", args.serial_out)

    children: list[subprocess.Popen] = []
    if args.launch_stack:
        children = launch_child_processes(args.reader_port, args.dashboard_port, args.dashboard_mode)

    source_mode = args.source
    if source_mode == "auto":
        source_mode = "websocket" if args.ws_url else "stdin"

    try:
        if source_mode == "websocket":
            if not args.ws_url:
                raise SystemExit("--ws-url or WOKWI_SERIAL_WS_URL is required for websocket mode")
            line_iterable = websocket_lines(args.ws_url)
        else:
            line_iterable = stdin_lines()

        for line in line_iterable:
            forward_packet(line, serial_port)

    except KeyboardInterrupt:
        logger.info("Bridge interrupted by user")
    finally:
        if serial_port is not None:
            serial_port.close()
        for process in children:
            if process.poll() is None:
                process.terminate()
        logger.info("Bridge shutdown complete")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())