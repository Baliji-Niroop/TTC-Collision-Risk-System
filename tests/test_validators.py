"""
Unit tests for src/validators.py
"""

from src.validators import detect_anomalies, validate_csv_line


def test_validate_csv_line_valid(sample_telemetry_line):
    """Test validation with valid telemetry line."""
    result = validate_csv_line(sample_telemetry_line)
    assert result is not None
    assert result["timestamp_ms"] == 1234567
    assert result["distance_cm"] == 150.5
    assert result["risk_class"] == 0


def test_validate_csv_line_invalid_field_count():
    """Test validation rejects lines with wrong field count."""
    # Too few fields
    result = validate_csv_line("1234,100.0,50.0")
    assert result is None
    
    # Too many fields
    result = validate_csv_line("1234,100,50,3.0,3.1,0,0.9,extra")
    assert result is None


def test_validate_csv_line_invalid_types():
    """Test validation rejects non-numeric values."""
    result = validate_csv_line("abc,100.0,50.0,3.0,3.1,0,0.9")
    assert result is None
    
    result = validate_csv_line("1234,invalid,50.0,3.0,3.1,0,0.9")
    assert result is None


def test_validate_csv_line_negative_values():
    """Test validation handles negative values appropriately."""
    # Negative TTC should be rejected
    result = validate_csv_line("1234,100.0,50.0,-1.0,3.1,0,0.9")
    assert result is None
    
    # Negative distance should be rejected
    result = validate_csv_line("1234,-100.0,50.0,3.0,3.1,0,0.9")
    assert result is None


def test_detect_anomalies_empty_buffer():
    """Test anomaly detection with empty buffer."""
    result = detect_anomalies([])
    assert result["anomalies"] == []


def test_detect_anomalies_normal_data():
    """Test anomaly detection with normal data."""
    normal_data = [
        {"distance_cm": 100.0, "speed_kmh": 50.0, "ttc_basic": 2.0, "confidence": 0.95},
        {"distance_cm": 95.0, "speed_kmh": 51.0, "ttc_basic": 1.9, "confidence": 0.94},
        {"distance_cm": 90.0, "speed_kmh": 52.0, "ttc_basic": 1.8, "confidence": 0.93},
    ]
    result = detect_anomalies(normal_data)
    assert result["anomaly_count"] == 0
    assert result["anomalies"] == []


def test_detect_anomalies_confidence_drop():
    """Test anomaly detection for sudden confidence drops."""
    data_with_drop = [
        {"distance_cm": 100.0, "speed_kmh": 50.0, "ttc_basic": 2.0, "confidence": 0.95},
        {"distance_cm": 95.0, "speed_kmh": 51.0, "ttc_basic": 1.9, "confidence": 0.20},  # Drop!
    ]
    result = detect_anomalies(data_with_drop)
    # Should detect the confidence anomaly
    assert result["anomaly_count"] >= 1
    assert any(a.get("type") == "confidence_drop" for a in result["anomalies"])
