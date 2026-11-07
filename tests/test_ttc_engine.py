"""
Unit tests for the core TTC kinematic calculation engine (src.ttc_engine).
"""

import pytest
from src.ttc_engine import (
    compute_ttc_basic,
    compute_ttc_extended,
    classify_risk,
    TTC_SAFE_CEILING_S,
)


def test_compute_ttc_basic_normal():
    """Test normal closing case: 30 meters gap closing at 10 m/s -> TTC = 3.0s."""
    ttc = compute_ttc_basic(distance_m=30.0, closing_speed_mps=10.0)
    assert ttc == 3.0


def test_compute_ttc_basic_zero_closing_speed():
    """Test zero closing speed: obstacle maintaining distance -> safe ceiling (99s)."""
    ttc = compute_ttc_basic(distance_m=20.0, closing_speed_mps=0.0)
    assert ttc == TTC_SAFE_CEILING_S


def test_compute_ttc_basic_vehicle_moving_away():
    """Test negative closing speed: lead vehicle moving away -> safe ceiling (99s)."""
    ttc = compute_ttc_basic(distance_m=25.0, closing_speed_mps=-5.0)
    assert ttc == TTC_SAFE_CEILING_S


def test_compute_ttc_basic_already_colliding():
    """Test zero or negative distance: vehicle is already touching/collided -> 0.0s."""
    assert compute_ttc_basic(distance_m=0.0, closing_speed_mps=10.0) == 0.0
    assert compute_ttc_basic(distance_m=-1.5, closing_speed_mps=10.0) == 0.0


def test_compute_ttc_extended_stops_safely():
    """Test extended TTC where vehicle braking halts car before collision -> 99.0s."""
    # Distance: 40m, closing speed: 10 m/s, deceleration: 5 m/s^2.
    # Stopping distance = v^2 / (2*a) = 100 / 10 = 10m < 40m. No collision!
    ttc = compute_ttc_extended(distance_m=40.0, closing_speed_mps=10.0, decel_mps2=5.0)
    assert ttc == TTC_SAFE_CEILING_S


def test_classify_risk_thresholds_and_weather():
    """Test risk classification across dry and wet conditions."""
    # Dry road (1.0x multiplier)
    assert classify_risk(ttc_seconds=1.2, road_condition=0) == 2  # CRITICAL (<= 1.5s)
    assert classify_risk(ttc_seconds=2.5, road_condition=0) == 1  # WARNING (1.5 - 3.0s)
    assert classify_risk(ttc_seconds=4.0, road_condition=0) == 0  # SAFE (> 3.0s)

    # Wet road (1.4x multiplier -> critical: 2.1s, warning: 4.2s)
    # At 1.8s, dry road would be WARNING, but wet road escalates to CRITICAL
    assert classify_risk(ttc_seconds=1.8, road_condition=1) == 2
