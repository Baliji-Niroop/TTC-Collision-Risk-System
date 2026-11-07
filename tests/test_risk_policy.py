"""Tests for the dashboard fallback risk policy."""

from pathlib import Path

import pytest

from src.risk_policy import classify_ttc_risk, resolve_dashboard_risk


@pytest.mark.parametrize(
    ("ttc_seconds", "expected"),
    [
        (3.1, 0),
        (3.0, 1),
        (2.0, 1),
        (1.5, 2),
        (0.0, 2),
    ],
)
def test_classify_ttc_risk_uses_inclusive_thresholds(ttc_seconds, expected):
    assert classify_ttc_risk(ttc_seconds, 3.0, 1.5) == expected


def test_classify_ttc_risk_rejects_invalid_threshold_order():
    with pytest.raises(ValueError, match="critical threshold"):
        classify_ttc_risk(2.0, 1.5, 1.5)


def test_classify_ttc_risk_rejects_non_finite_ttc():
    with pytest.raises(ValueError, match="finite"):
        classify_ttc_risk(float("nan"), 3.0, 1.5)


def test_dashboard_fallback_risk_overrides_packet_risk():
    assert resolve_dashboard_risk(0, 1.0, False, 3.0, 1.5) == 2


def test_dashboard_resolves_risk_before_dispatching_alerts():
    source = (Path(__file__).parents[1] / "src" / "dashboard.py").read_text(
        encoding="utf-8"
    )

    assert "risk = resolve_dashboard_risk(" in source
    assert source.index("risk = resolve_dashboard_risk(") < source.index(
        "check_and_alert(risk, row)"
    )
