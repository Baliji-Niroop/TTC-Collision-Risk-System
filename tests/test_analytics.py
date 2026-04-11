"""
Unit tests for TTC risk classification thresholds.
"""

from src.config import get_risk_class


def test_classify_risk_basic_critical():
    """Test CRITICAL risk classification."""
    # TTC <= 1.5s should be CRITICAL
    assert get_risk_class(0.5) == 2
    assert get_risk_class(1.0) == 2
    assert get_risk_class(1.5) == 2


def test_classify_risk_basic_warning():
    """Test WARNING risk classification."""
    # 1.5s < TTC <= 3.0s should be WARNING
    assert get_risk_class(1.6) == 1
    assert get_risk_class(2.0) == 1
    assert get_risk_class(3.0) == 1


def test_classify_risk_basic_safe():
    """Test SAFE risk classification."""
    # TTC > 3.0s should be SAFE
    assert get_risk_class(3.1) == 0
    assert get_risk_class(5.0) == 0
    assert get_risk_class(10.0) == 0


def test_classify_risk_basic_boundary_conditions():
    """Test boundary conditions at exactly 1.5s and 3.0s."""
    assert get_risk_class(1.5) == 2  # Exactly critical threshold
    assert get_risk_class(3.0) == 1  # Exactly warning threshold
    assert get_risk_class(1.50001) == 1  # Just above critical
