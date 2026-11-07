"""Risk-resolution rules shared by dashboard decision paths."""

from __future__ import annotations

import math


def classify_ttc_risk(
    ttc_seconds: float,
    warning_threshold_s: float,
    critical_threshold_s: float,
) -> int:
    """Return SAFE (0), WARNING (1), or CRITICAL (2) for a TTC value."""
    if not all(
        math.isfinite(value)
        for value in (ttc_seconds, warning_threshold_s, critical_threshold_s)
    ):
        raise ValueError("TTC and thresholds must be finite")
    if critical_threshold_s >= warning_threshold_s:
        raise ValueError("critical threshold must be less than warning threshold")
    if ttc_seconds <= critical_threshold_s:
        return 2
    if ttc_seconds <= warning_threshold_s:
        return 1
    return 0


def resolve_dashboard_risk(
    predicted_risk: int,
    ttc_seconds: float,
    model_available: bool,
    warning_threshold_s: float,
    critical_threshold_s: float,
) -> int:
    """Use model output when available; otherwise apply dashboard thresholds."""
    if model_available:
        return int(predicted_risk)
    return classify_ttc_risk(ttc_seconds, warning_threshold_s, critical_threshold_s)
