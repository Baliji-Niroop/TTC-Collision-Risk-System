"""
Telemetry Data Schema & Parser

Defines the 7-field telemetry contract used throughout the system.
Provides functions to parse raw CSV data into structured records.

Format: timestamp_ms, distance_cm, speed_kmh, ttc_basic, ttc_ext, risk_class, confidence
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from config import TELEMETRY_FIELDS, TELEMETRY_FIELD_COUNT


def _coerce_float(value: Any) -> float:
    return float(value)


def _coerce_int(value: Any) -> int:
    return int(float(value))


def parse_packet(line: str) -> Optional[Dict[str, Any]]:
    """Parse a canonical 7-field CSV packet into a telemetry dictionary."""
    if not line or not isinstance(line, str):
        return None

    parts = [part.strip() for part in line.strip().split(",")]
    if len(parts) != TELEMETRY_FIELD_COUNT:
        return None

    try:
        return {
            "timestamp_ms": _coerce_float(parts[0]),
            "distance_cm": _coerce_float(parts[1]),
            "speed_kmh": _coerce_float(parts[2]),
            "ttc_basic": _coerce_float(parts[3]),
            "ttc_ext": _coerce_float(parts[4]),
            "risk_class": _coerce_int(parts[5]),
            "confidence": _coerce_float(parts[6]),
        }
    except (TypeError, ValueError):
        return None


def format_packet(row: Dict[str, Any]) -> str:
    """Format a telemetry row into the canonical 7-field CSV packet."""
    timestamp_ms = int(round(float(row.get("timestamp_ms", 0.0))))
    distance_cm = float(row.get("distance_cm", 0.0))
    speed_kmh = float(row.get("speed_kmh", 0.0))
    ttc_basic = float(row.get("ttc_basic", 99.0))
    ttc_ext = float(row.get("ttc_ext", 99.0))
    risk_class = int(float(row.get("risk_class", 0)))
    confidence = max(0.0, min(1.0, float(row.get("confidence", 1.0))))

    return (
        f"{timestamp_ms},"
        f"{distance_cm:.2f},"
        f"{speed_kmh:.2f},"
        f"{ttc_basic:.2f},"
        f"{ttc_ext:.2f},"
        f"{risk_class:d},"
        f"{confidence:.2f}"
    )


def canonical_row(
    timestamp_ms: float,
    distance_cm: float,
    speed_kmh: float,
    ttc_basic: float,
    ttc_ext: float,
    risk_class: int,
    confidence: float,
) -> Dict[str, Any]:
    """Build a canonical telemetry row dictionary."""
    return {
        "timestamp_ms": float(timestamp_ms),
        "distance_cm": float(distance_cm),
        "speed_kmh": float(speed_kmh),
        "ttc_basic": float(ttc_basic),
        "ttc_ext": float(ttc_ext),
        "risk_class": int(risk_class),
        "confidence": float(confidence),
    }


def coerce_telemetry_row(row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Normalize a row-like object into canonical telemetry keys."""
    if not row:
        return None

    try:
        return canonical_row(
            row["timestamp_ms"],
            row["distance_cm"],
            row["speed_kmh"],
            row["ttc_basic"],
            row["ttc_ext"],
            row["risk_class"],
            row["confidence"],
        )
    except KeyError:
        return None


def packet_columns() -> list[str]:
    """Return the canonical telemetry column order."""
    return list(TELEMETRY_FIELDS)
