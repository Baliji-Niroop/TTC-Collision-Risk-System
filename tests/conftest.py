"""
pytest configuration and shared fixtures for TTC project tests.
"""
import pytest
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def sample_telemetry_line():
    """Sample valid 7-field telemetry CSV line."""
    return "1234567,150.5,45.2,3.32,3.45,0,0.98"


@pytest.fixture
def sample_telemetry_dict():
    """Sample telemetry data as dictionary."""
    return {
        "timestamp_ms": 1234567,
        "distance_cm": 150.5,
        "speed_kmh": 45.2,
        "ttc_basic": 3.32,
        "ttc_ext": 3.45,
        "risk_class": 0,
        "confidence": 0.98,
    }


@pytest.fixture
def sample_critical_telemetry():
    """Sample CRITICAL risk telemetry."""
    return {
        "timestamp_ms": 1234567,
        "distance_cm": 25.0,
        "speed_kmh": 60.0,
        "ttc_basic": 1.2,
        "ttc_ext": 1.3,
        "risk_class": 2,
        "confidence": 0.95,
    }


@pytest.fixture
def mock_csv_file(tmp_path):
    """Create a temporary CSV file with sample telemetry data."""
    csv_file = tmp_path / "test_telemetry.csv"
    csv_file.write_text(
        "timestamp_ms,distance_cm,speed_kmh,ttc_basic,ttc_ext,risk_class,confidence\n"
        "1000000,200.5,50.0,4.01,4.10,0,0.99\n"
        "1000200,190.3,50.1,3.79,3.85,0,0.98\n"
        "1000400,180.0,50.2,3.58,3.62,0,0.97\n"
        "1000600,150.0,51.0,2.94,3.01,1,0.96\n"
        "1000800,100.0,52.0,1.92,2.05,1,0.95\n"
        "1001000,50.0,53.0,0.94,1.10,2,0.94\n"
    )
    return csv_file


@pytest.fixture
def mock_model(tmp_path):
    """Create a mock ML model pickle file."""
    import joblib
    
    # Simple mock classifier
    class MockClassifier:
        def predict(self, X):
            import numpy as np
            return np.array([0] * len(X))
        
        def predict_proba(self, X):
            import numpy as np
            return np.array([[0.8, 0.15, 0.05]] * len(X))
    
    model_file = tmp_path / "mock_model.pkl"
    joblib.dump(MockClassifier(), model_file)
    return model_file
