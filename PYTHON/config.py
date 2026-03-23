"""
config.py
Centralized settings for the TTC Collision Risk system.
All thresholds, paths, and tunable parameters live here.
"""

from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)

# --- Paths ---
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
MODEL_PATH = ROOT_DIR / "MODELS" / "ml_model.pkl"
DATA_PATH = ROOT_DIR / "LOGS" / "live_data.txt"
LOG_DIR = ROOT_DIR / "LOGS"
CONFIG_FILE = ROOT_DIR / "config.json"

LOG_DIR.mkdir(parents=True, exist_ok=True)

# --- Risk classification ---
# TTC thresholds define the three risk zones
RISK_THRESHOLDS = {
    "critical": 1.5,       # TTC <= 1.5 s  ->  CRITICAL
    "warning": 3.0,        # 1.5 < TTC <= 3.0  ->  WARNING
    "safe": float("inf")   # TTC > 3.0  ->  SAFE
}

RISK_LABELS = {0: "SAFE", 1: "WARNING", 2: "CRITICAL"}
RISK_INVERSE = {v: k for k, v in RISK_LABELS.items()}

RISK_COLORS = {
    0: ("SAFE", "#1a7a2e"),      # Green
    1: ("WARNING", "#b36b00"),    # Amber
    2: ("CRITICAL", "#b71c1c"),   # Red
}

# --- Dashboard & UI ---
DASHBOARD_CONFIG = {
    "page_title": "TTC Collision Risk Dashboard",
    "page_icon": "🚗",
    "layout": "wide",
    "max_buffer_points": 120,
    "refresh_interval_sec": 0.6,
    "log_display_rows": 30,
}

# --- Serial communication ---
SERIAL_CONFIG = {
    "baud_rate": 115200,
    "timeout": 2,
    "encoding": "utf-8",
    "expected_fields": 7,
}

# --- Simulator defaults ---
SIMULATOR_CONFIG = {
    "initial_distance_m": 40.0,
    "closing_speed_kmh": 15.0,
    "deceleration_ms2": 5.0,
    "loop_dt": 0.3,
    "reset_distance_m": 0.3,
}

# --- Alerting ---
ALERT_CONFIG = {
    "enable_alerts": True,
    "critical_alert_every_n_events": 1,
    "warning_alert_every_n_events": 5,
    "min_ttc_alert_threshold": 1.0,
}

# --- Anomaly detection ---
ANOMALY_CONFIG = {
    "enable_detection": True,
    "max_speed_kmh": 150.0,
    "min_ttc_possible": 0.1,
    "max_confidence_drop": 0.5,
    "outlier_zscore_threshold": 3.0,
}

# --- Logging ---
LOGGING_CONFIG = {
    "log_level": "INFO",
    "log_file": LOG_DIR / "ttc_system.log",
    "max_log_size_mb": 50,
    "backup_count": 5,
    "log_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
}


# --- Helper functions ---

def get_risk_class(ttc: float) -> int:
    """Return 0 (SAFE), 1 (WARNING), or 2 (CRITICAL) based on TTC."""
    if ttc <= RISK_THRESHOLDS["critical"]:
        return 2
    elif ttc <= RISK_THRESHOLDS["warning"]:
        return 1
    return 0


def get_risk_label(risk_class: int) -> str:
    """Return the text label for a numeric risk class."""
    return RISK_LABELS.get(risk_class, "UNKNOWN")


def load_config_from_file():
    """Load overrides from config.json if it exists."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load config from {CONFIG_FILE}: {e}")
    return {}


def save_config_to_file(config_dict: dict):
    """Write current config to config.json for persistence."""
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config_dict, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Failed to save config to {CONFIG_FILE}: {e}")
