"""
ttc_engine.py - Core Time-To-Collision (TTC) Kinematic Engine

Provides pure mathematical functions to compute Time-To-Collision and classify
collision risk based on distance, closing speed, and deceleration.

Units:
    - Distance: meters (m)
    - Velocity / Speed: meters per second (m/s) or kilometers per hour (km/h)
    - Deceleration / Acceleration: meters per second squared (m/s^2)
    - Time: seconds (s)
"""

from __future__ import annotations

import math


# Default ADAS Time-To-Collision risk thresholds (seconds)
TTC_CRITICAL_THRESHOLD_S: float = 1.5
TTC_WARNING_THRESHOLD_S: float = 3.0
TTC_SAFE_CEILING_S: float = 99.0

# Numerical minimum closing speed to avoid division by zero or jitter
MIN_CLOSING_SPEED_MPS: float = 0.10


def compute_ttc_basic(distance_m: float, closing_speed_mps: float) -> float:
    """
    Compute basic Time-To-Collision assuming constant closing velocity.

    Formula:
        TTC = distance / closing_speed

    Args:
        distance_m: Distance to the obstacle ahead in meters (m).
        closing_speed_mps: Relative closing speed in meters per second (m/s).
                           Positive values mean vehicles are closing the gap.
                           Zero or negative values mean distance is maintained or increasing.

    Returns:
        float: Time-to-collision in seconds (s).
               Returns 0.0 if already colliding (distance <= 0).
               Returns 99.0 if closing speed is too low, stationary, or opening.
    """
    if distance_m <= 0.0:
        return 0.0

    if closing_speed_mps <= MIN_CLOSING_SPEED_MPS:
        return TTC_SAFE_CEILING_S

    ttc = distance_m / closing_speed_mps
    return round(min(ttc, TTC_SAFE_CEILING_S), 2)


def compute_ttc_extended(
    distance_m: float,
    closing_speed_mps: float,
    decel_mps2: float = 5.0,
) -> float:
    """
    Compute extended Time-To-Collision incorporating vehicle deceleration capability.

    Derived from kinematics:
        d = v_closing * t - 0.5 * a * t^2
    Rearranged into standard quadratic:
        0.5 * a * t^2 - v_closing * t + d = 0
    Solving for the earliest collision time t:
        discriminant = v_closing^2 - 2 * a * d

    Args:
        distance_m: Distance to the obstacle ahead in meters (m).
        closing_speed_mps: Relative closing speed in meters per second (m/s).
        decel_mps2: Deceleration available in m/s^2 (default: 5.0 m/s^2).

    Returns:
        float: Extended TTC in seconds (s).
               Returns 99.0 if deceleration halts the vehicle before impact (discriminant < 0).
               Falls back to compute_ttc_basic if decel_mps2 <= 0.01.
    """
    if distance_m <= 0.0:
        return 0.0

    if closing_speed_mps <= MIN_CLOSING_SPEED_MPS:
        return TTC_SAFE_CEILING_S

    if decel_mps2 <= 0.01:
        return compute_ttc_basic(distance_m, closing_speed_mps)

    discriminant = (closing_speed_mps ** 2) - (2.0 * decel_mps2 * distance_m)

    # If discriminant < 0, braking stops the vehicle before collision occurs
    if discriminant < 0.0:
        return TTC_SAFE_CEILING_S

    t_collision = (closing_speed_mps - math.sqrt(discriminant)) / decel_mps2
    if t_collision < 0.0:
        return TTC_SAFE_CEILING_S

    return round(min(t_collision, TTC_SAFE_CEILING_S), 2)


def classify_risk(
    ttc_seconds: float,
    road_condition: int = 0,
    critical_threshold_s: float = TTC_CRITICAL_THRESHOLD_S,
    warning_threshold_s: float = TTC_WARNING_THRESHOLD_S,
) -> int:
    """
    Classify collision risk level into standard ADAS states.

    Road condition multipliers:
        0 = Dry asphalt (1.0x)
        1 = Wet asphalt (1.4x - requires earlier warning due to lower friction)
        2 = Gravel (1.6x)
        3 = Snow / Ice (2.0x)

    Risk Levels:
        0: SAFE     (TTC > warning threshold)
        1: WARNING  (critical < TTC <= warning threshold)
        2: CRITICAL (TTC <= critical threshold)

    Args:
        ttc_seconds: Estimated time-to-collision in seconds.
        road_condition: Surface condition flag (0=Dry, 1=Wet, 2=Gravel, 3=Ice).
        critical_threshold_s: Base critical threshold in seconds (default: 1.5s).
        warning_threshold_s: Base warning threshold in seconds (default: 3.0s).

    Returns:
        int: Risk class (0=SAFE, 1=WARNING, 2=CRITICAL).
    """
    multiplier_map = {0: 1.0, 1: 1.4, 2: 1.6, 3: 2.0}
    multiplier = multiplier_map.get(road_condition, 1.0)

    adjusted_critical = critical_threshold_s * multiplier
    adjusted_warning = warning_threshold_s * multiplier

    if ttc_seconds <= adjusted_critical:
        return 2  # CRITICAL
    elif ttc_seconds <= adjusted_warning:
        return 1  # WARNING
    return 0  # SAFE
