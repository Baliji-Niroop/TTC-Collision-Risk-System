"""
Configuration Module
====================
Centralized configuration for the TTC Collision Risk Prediction System.
Manages constants, thresholds, and system parameters.
"""

from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)

# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ PATHS
# ╚═══════════════════════════════════════════════════════════════════════════╝
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
MODEL_PATH = ROOT_DIR / "MODELS" / "ml_model.pkl"
DATA_PATH = ROOT_DIR / "LOGS" / "live_data.txt"
LOG_DIR = ROOT_DIR / "LOGS"
CONFIG_FILE = ROOT_DIR / "config.json"

# Ensure critical directories exist
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ RISK CLASSIFICATION
# ╚═══════════════════════════════════════════════════════════════════════════╝
# These thresholds define the risk zones based on TTC values (Time-to-Collision)
RISK_THRESHOLDS = {
    "critical": 1.5,   # TTC <= 1.5 s → CRITICAL
    "warning": 3.0,    # 1.5 s < TTC <= 3.0 s → WARNING
    "safe": float("inf")  # TTC > 3.0 s → SAFE
}

# Risk class labels
RISK_LABELS = {0: "SAFE", 1: "WARNING", 2: "CRITICAL"}
RISK_INVERSE = {v: k for k, v in RISK_LABELS.items()}

# Risk colors for UI display
RISK_COLORS = {
    0: ("SAFE", "#1a7a2e"),      # Green
    1: ("WARNING", "#b36b00"),    # Amber
    2: ("CRITICAL", "#b71c1c"),   # Red
}

# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ DASHBOARD & UI
# ╚═══════════════════════════════════════════════════════════════════════════╝
DASHBOARD_CONFIG = {
    "page_title": "TTC Collision Risk Dashboard",
    "page_icon": "🚗",
    "layout": "wide",
    "max_buffer_points": 120,  # Number of data points in rolling chart
    "refresh_interval_sec": 0.6,  # Dashboard refresh rate
    "log_display_rows": 30,  # Recent events to show
}

# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ SERIAL COMMUNICATION
# ╚═══════════════════════════════════════════════════════════════════════════╝
SERIAL_CONFIG = {
    "baud_rate": 115200,
    "timeout": 2,  # seconds
    "encoding": "utf-8",
    "expected_fields": 7,
}

# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ SIMULATOR
# ╚═══════════════════════════════════════════════════════════════════════════╝
SIMULATOR_CONFIG = {
    "initial_distance_m": 40.0,
    "closing_speed_kmh": 15.0,
    "deceleration_ms2": 5.0,
    "loop_dt": 0.3,
    "reset_distance_m": 0.3,
}

# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ ALERTING
# ╚═══════════════════════════════════════════════════════════════════════════╝
ALERT_CONFIG = {
    "enable_alerts": True,
    "critical_alert_every_n_events": 1,  # Alert on every CRITICAL event
    "warning_alert_every_n_events": 5,   # Alert on every 5th WARNING event
    "min_ttc_alert_threshold": 1.0,  # Alert if TTC goes below this
}

# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ ANOMALY DETECTION
# ╚═══════════════════════════════════════════════════════════════════════════╝
ANOMALY_CONFIG = {
    "enable_detection": True,
    "max_speed_kmh": 150.0,  # Unrealistic speed
    "min_ttc_possible": 0.1,  # Can't have negative or near-zero TTC
    "max_confidence_drop": 0.5,  # Large swings in confidence
    "outlier_zscore_threshold": 3.0,
}

# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ LOGGING
# ╚═══════════════════════════════════════════════════════════════════════════╝
LOGGING_CONFIG = {
    "log_level": "INFO",  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    "log_file": LOG_DIR / "ttc_system.log",
    "max_log_size_mb": 50,
    "backup_count": 5,
    "log_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
}

# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ HELPER FUNCTIONS
# ╚═══════════════════════════════════════════════════════════════════════════╝

def get_risk_class(ttc: float) -> int:
    """
    Classify risk based on TTC value.
    
    Args:
        ttc: Time-to-collision in seconds
        
    Returns:
        Risk class: 0 (SAFE), 1 (WARNING), 2 (CRITICAL)
    """
    if ttc <= RISK_THRESHOLDS["critical"]:
        return 2
    elif ttc <= RISK_THRESHOLDS["warning"]:
        return 1
    else:
        return 0


def get_risk_label(risk_class: int) -> str:
    """Get human-readable risk label."""
    return RISK_LABELS.get(risk_class, "UNKNOWN")


def load_config_from_file():
    """Load configuration from JSON file if it exists."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load config from {CONFIG_FILE}: {e}")
    return {}


def save_config_to_file(config_dict: dict):
    """Save configuration to JSON file."""
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config_dict, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Failed to save config to {CONFIG_FILE}: {e}")
