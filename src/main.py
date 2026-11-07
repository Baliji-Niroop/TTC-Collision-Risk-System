"""
main.py - Central Entry Point for TTC Collision Risk System

Allows running the end-to-end demo, replaying validation sessions,
launching the interactive dashboard, or running system verification checks.

Usage:
    python src/main.py --demo              # Run live simulated collision scenario demo
    python src/main.py --replay <file.csv> # Replay a recorded or synthetic session CSV
    python src/main.py --dashboard         # Launch Streamlit dashboard UI
    python src/main.py --check             # Run quality gates, pytest, and protocol tests
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

# Setup system paths
ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = Path(__file__).resolve().parent

for p in (ROOT_DIR, SRC_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

try:
    from ttc_engine import compute_ttc_basic, compute_ttc_extended, classify_risk
    from config import DATASET_DIR, RISK_LABELS, RISK_THRESHOLDS
except ImportError:
    from src.ttc_engine import compute_ttc_basic, compute_ttc_extended, classify_risk
    from src.config import DATASET_DIR, RISK_LABELS, RISK_THRESHOLDS


def run_demo(steps: int = 20, delay_s: float = 0.25) -> None:
    """
    Run a terminal-based live demonstration showing dynamic TTC calculation
    and risk state progression during vehicle approach.
    """
    print("\n" + "=" * 72)
    print("  TTC (TIME-TO-COLLISION) SYSTEM DEMONSTRATION")
    print("=" * 72)
    print("Simulating host vehicle approaching an obstacle:")
    print(f"Risk Thresholds: CRITICAL <= {RISK_THRESHOLDS['critical']}s | WARNING <= {RISK_THRESHOLDS['warning']}s\n")
    print(f"{'Time':^8} | {'Distance':^10} | {'Rel Speed':^11} | {'TTC Basic':^11} | {'TTC Ext':^11} | {'Risk State':^10}")
    print("-" * 72)

    # Simulated deceleration approach scenario: gap closes from 40m down to 2m
    initial_dist = 40.0
    closing_speed = 12.0  # m/s (~43.2 km/h)
    decel_mps2 = 5.0     # m/s^2

    dist = initial_dist
    dt = 0.20

    for step in range(steps):
        t_sec = step * dt
        # Distance closes over time
        dist = max(initial_dist - (closing_speed * t_sec), 1.0)

        ttc_basic = compute_ttc_basic(dist, closing_speed)
        ttc_ext = compute_ttc_extended(dist, closing_speed, decel_mps2)
        risk_class = classify_risk(ttc_basic)
        risk_name = RISK_LABELS.get(risk_class, "UNKNOWN")

        # Color highlight indicator
        risk_tag = f"[{risk_name}]"
        print(f"{t_sec:6.2f} s | {dist:8.2f} m | {closing_speed:8.2f} m/s | {ttc_basic:8.2f} s  | {ttc_ext:8.2f} s  | {risk_tag:^10}")

        if dist <= 1.5 or ttc_basic <= 0.3:
            print("-" * 72)
            print(">>> Emergency braking threshold reached / vehicle at minimum safe gap.")
            break

        time.sleep(delay_s)

    print("=" * 72)
    print("Demo complete. To view interactive UI graphs, run: python src/main.py --dashboard\n")


def run_replay(csv_file: Path) -> None:
    """Replay an existing session CSV through the analytics pipeline."""
    if not csv_file.exists():
        print(f"[ERROR] Replay CSV file not found: {csv_file}")
        sys.exit(1)

    print(f"Replaying session from: {csv_file}")
    replay_script = SRC_DIR / "replay_runner.py"
    result = subprocess.run(
        [sys.executable, str(replay_script), "--input", str(csv_file)]
    )
    if result.returncode != 0:
        print("[ERROR] Replay failed.")
        sys.exit(result.returncode)


def run_dashboard() -> None:
    """Launch Streamlit web dashboard."""
    dashboard_script = SRC_DIR / "dashboard.py"
    print("Launching Streamlit dashboard...")
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(dashboard_script)])


def run_checks() -> None:
    """Run full test and protocol verification suite."""
    print("=" * 60)
    print("Running Quality Verification Gate...")
    print("=" * 60)

    # 1. Pytest
    print("\n[1/4] Running Pytest Unit Tests...")
    res_pytest = subprocess.run([sys.executable, "-m", "pytest", "-q"])
    if res_pytest.returncode != 0:
        print("[FAIL] Pytest failed.")
        sys.exit(res_pytest.returncode)
    print("[PASS] Unit tests passed.")

    # 2. Protocol Contract Test
    print("\n[2/4] Checking 7-Field Telemetry Contract...")
    protocol_script = ROOT_DIR / "validation" / "protocol_contract_test.py"
    res_proto = subprocess.run([sys.executable, str(protocol_script)])
    if res_proto.returncode != 0:
        print("[FAIL] Protocol contract test failed.")
        sys.exit(res_proto.returncode)

    # 3. Pin Validator
    print("\n[3/4] Validating Pin Mapping Consistency...")
    pin_script = ROOT_DIR / "validation" / "pin_validator.py"
    res_pins = subprocess.run([sys.executable, str(pin_script)])
    if res_pins.returncode == 1:
        print("[WARN] Pin mapping validation reported non-critical warnings.")
    elif res_pins.returncode != 0:
        print("[FAIL] Pin mapping validation failed.")
        sys.exit(res_pins.returncode)

    print("\n[4/4] Running Flake8...")
    res_lint = subprocess.run(
        [
            sys.executable,
            "-m",
            "flake8",
            "src",
            "ml",
            "validation",
            "bridge",
            "tests",
        ]
    )
    if res_lint.returncode != 0:
        print("[FAIL] Flake8 failed.")
        sys.exit(res_lint.returncode)

    print("\nVerification suite completed.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="TTC Collision Risk System - Central Command & Demo Launcher"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run terminal demonstration of real-time TTC calculation",
    )
    parser.add_argument(
        "--replay",
        type=Path,
        nargs="?",
        const=DATASET_DIR / "synthetic_ttc_validation.csv",
        help="Replay a CSV session (defaults to data/synthetic_ttc_validation.csv)",
    )
    parser.add_argument(
        "--dashboard",
        action="store_true",
        help="Launch the interactive Streamlit web dashboard",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run pytest and protocol verification checks",
    )

    args = parser.parse_args()

    if args.demo:
        run_demo(steps=15, delay_s=0.1)
    elif args.replay:
        run_replay(args.replay)
    elif args.dashboard:
        run_dashboard()
    elif args.check:
        run_checks()
    else:
        # Default behavior: run demo if no arguments provided
        run_demo(steps=12, delay_s=0.1)


if __name__ == "__main__":
    main()
