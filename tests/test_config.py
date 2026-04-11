"""
Unit tests for src/config.py
"""
import pytest
from src import config


def test_telemetry_fields_count():
    """Verify telemetry field count is 7."""
    assert config.TELEMETRY_FIELD_COUNT == 7
    assert len(config.TELEMETRY_FIELDS) == 7


def test_telemetry_fields_order():
    """Verify canonical telemetry field order."""
    expected_order = (
        "timestamp_ms",
        "distance_cm",
        "speed_kmh",
        "ttc_basic",
        "ttc_ext",
        "risk_class",
        "confidence",
    )
    assert config.TELEMETRY_FIELDS == expected_order


def test_risk_thresholds():
    """Verify TTC risk thresholds match firmware."""
    assert config.RISK_THRESHOLDS["critical"] == 1.5
    assert config.RISK_THRESHOLDS["warning"] == 3.0
    assert config.RISK_THRESHOLDS["safe"] == float("inf")


def test_risk_labels():
    """Verify risk label mappings."""
    assert config.RISK_LABELS[0] == "SAFE"
    assert config.RISK_LABELS[1] == "WARNING"
    assert config.RISK_LABELS[2] == "CRITICAL"


def test_get_risk_class():
    """Test risk classification function."""
    # CRITICAL
    assert config.get_risk_class(0.5) == 2
    assert config.get_risk_class(1.5) == 2
    
    # WARNING
    assert config.get_risk_class(2.0) == 1
    assert config.get_risk_class(3.0) == 1
    
    # SAFE
    assert config.get_risk_class(3.5) == 0
    assert config.get_risk_class(10.0) == 0


def test_serial_config():
    """Verify serial configuration."""
    assert config.SERIAL_CONFIG["baud_rate"] == 115200
    assert config.SERIAL_CONFIG["expected_fields"] == 7


def test_physics_config_exists():
    """Verify PHYSICS_CONFIG section exists."""
    assert "default_deceleration_ms2" in config.PHYSICS_CONFIG
    assert config.PHYSICS_CONFIG["default_deceleration_ms2"] == 5.0


def test_validation_config_exists():
    """Verify VALIDATION_CONFIG section exists."""
    assert "capture_duration_sec" in config.VALIDATION_CONFIG
    assert "random_seed" in config.VALIDATION_CONFIG
    assert config.VALIDATION_CONFIG["random_seed"] == 42


def test_anomaly_config_expanded():
    """Verify ANOMALY_CONFIG has physical constraints."""
    assert "max_vehicle_speed_kmh" in config.ANOMALY_CONFIG
    assert "max_acceleration_ms2" in config.ANOMALY_CONFIG
    assert "max_deceleration_ms2" in config.ANOMALY_CONFIG
