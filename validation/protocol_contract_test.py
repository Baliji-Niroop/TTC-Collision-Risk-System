"""
protocol_contract_test.py
Strict canonical telemetry contract checks.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from validators import validate_csv_line  # noqa: E402


def _expect_valid(line: str) -> bool:
    return validate_csv_line(line) is not None


def _expect_invalid(line: str) -> bool:
    return validate_csv_line(line) is None


def main() -> None:
    tests = {
        "canonical_packet_valid": _expect_valid("1000,2500.0,35.0,2.8,2.5,1,0.91"),
        "wrong_field_count_missing": _expect_invalid("1000,2500.0,35.0,2.8,2.5,1"),
        "wrong_field_count_extra": _expect_invalid(
            "1000,2500.0,35.0,2.8,2.5,1,0.91,extra"
        ),
        "legacy_alias_risk_phys": _expect_invalid(
            "1000,2500.0,35.0,2.8,2.5,risk_phys,0.91"
        ),
        "header_line_rejected": _expect_invalid(
            "timestamp_ms,distance_cm,speed_kmh,ttc_basic,ttc_ext,risk_class,confidence"
        ),
        "non_numeric_token_rejected": _expect_invalid(
            "1000,2500.0,35.0,2.8,2.5,WARNING,0.91"
        ),
    }

    passed = sum(1 for ok in tests.values() if ok)
    total = len(tests)

    for name, ok in tests.items():
        print(f"{'PASS' if ok else 'FAIL'}: {name}")

    print(f"\nProtocol tests: {passed}/{total} passed")
    if passed != total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
