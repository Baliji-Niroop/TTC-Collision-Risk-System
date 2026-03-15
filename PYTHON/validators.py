"""
Data Validation Module
======================
Provides validation and sanitization for telemetry data.
Detects anomalies and malformed data.
"""

from typing import Optional, Dict, Any
from config import ANOMALY_CONFIG, SERIAL_CONFIG
from logger import get_logger
import statistics

logger = get_logger(__name__)


def validate_telemetry_line(line: str) -> bool:
    """
    Validate that a telemetry line has the expected format and field count.
    
    Args:
        line: Raw CSV line from sensor
        
    Returns:
        True if valid, False otherwise
    """
    if not line or not isinstance(line, str):
        return False
    
    parts = line.split(",")
    if len(parts) != SERIAL_CONFIG["expected_fields"]:
        logger.warning(f"Invalid field count: expected {SERIAL_CONFIG['expected_fields']}, got {len(parts)}")
        return False
    
    return True


def sanitize_telemetry_data(row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Validate and sanitize telemetry data.
    
    Checks for:
    - Out-of-range values
    - Unrealistic speed
    - Impossible TTC values
    - Confidence drops
    
    Args:
        row: Parsed telemetry row
        
    Returns:
        Sanitized row if valid, None if anomaly detected
    """
    if not row:
        return None
    
    try:
        # Check required fields
        required_fields = ["distance_cm", "speed_kmh", "ttc_basic", "ttc_ext", "confidence"]
        if not all(field in row for field in required_fields):
            logger.warning(f"Missing required fields in row: {row.keys()}")
            return None
        
        # Validate ranges
        distance = float(row["distance_cm"])
        speed = float(row["speed_kmh"])
        ttc_basic = float(row["ttc_basic"])
        confidence = float(row["confidence"])
        
        # Check unrealistic values - REJECT these rows
        if speed > ANOMALY_CONFIG["max_speed_kmh"]:
            logger.warning(f"Unrealistic speed detected: {speed} km/h")
            return None
            
        if ttc_basic < ANOMALY_CONFIG["min_ttc_possible"] and ttc_basic < 99.0:
            logger.warning(f"Impossible TTC detected: {ttc_basic} s")
            return None
            
        if distance < 0:
            logger.warning(f"Negative distance detected: {distance} cm")
            return None
            
        if confidence < 0 or confidence > 1.0:
            logger.warning(f"Invalid confidence: {confidence}")
            return None
        
        row["anomaly_flag"] = False
        return row
        
    except (ValueError, TypeError) as e:
        logger.error(f"Data type error during validation: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        return None


def detect_anomalies(data_buffer: list) -> Dict[str, Any]:
    """
    Detect statistical anomalies in the data buffer.
    
    Uses Z-score method and other heuristics.
    
    Args:
        data_buffer: List of recent telemetry readings
        
    Returns:
        Dictionary with anomaly flags and statistics
    """
    if not data_buffer or len(data_buffer) < 3:
        return {"anomalies": []}
    
    anomalies = []
    
    try:
        # Extract TTC values
        ttc_values = [d.get("ttc_basic", 0) for d in data_buffer if d.get("ttc_basic", 0) < 99.0]
        
        if len(ttc_values) >= 3:
            mean_ttc = statistics.mean(ttc_values)
            stdev_ttc = statistics.stdev(ttc_values)
            
            # Check for outliers
            if stdev_ttc > 0:
                for i, row in enumerate(data_buffer):
                    ttc = row.get("ttc_basic", 0)
                    if ttc < 99.0:
                        z_score = abs((ttc - mean_ttc) / stdev_ttc)
                        if z_score > ANOMALY_CONFIG["outlier_zscore_threshold"]:
                            anomalies.append({
                                "index": i,
                                "type": "ttc_outlier",
                                "value": ttc,
                                "z_score": z_score
                            })
        
        # Check for sudden confidence drops
        if len(data_buffer) >= 2:
            for i in range(1, len(data_buffer)):
                prev_conf = data_buffer[i-1].get("confidence", 1.0)
                curr_conf = data_buffer[i].get("confidence", 1.0)
                drop = prev_conf - curr_conf
                
                if drop > ANOMALY_CONFIG["max_confidence_drop"]:
                    anomalies.append({
                        "index": i,
                        "type": "confidence_drop",
                        "drop": drop
                    })
        
        if anomalies:
            logger.warning(f"Detected {len(anomalies)} anomalies in buffer")
        
        return {
            "anomalies": anomalies,
            "mean_ttc": mean_ttc if len(ttc_values) >= 3 else None,
            "anomaly_count": len(anomalies)
        }
        
    except Exception as e:
        logger.error(f"Error during anomaly detection: {e}")
        return {"anomalies": [], "error": str(e)}


def validate_csv_line(line: str) -> Optional[Dict[str, Any]]:
    """
    Parse and validate a CSV line from telemetry source.
    
    Args:
        line: Raw CSV line
        
    Returns:
        Parsed and validated data dict, or None if invalid
    """
    if not validate_telemetry_line(line):
        return None
    
    try:
        parts = [p.strip() for p in line.split(",")]
        
        row = {
            "timestamp_ms": float(parts[0]),
            "distance_cm": float(parts[1]),
            "speed_kmh": float(parts[2]),
            "ttc_basic": float(parts[3]),
            "ttc_ext": float(parts[4]),
            "risk_phys": int(float(parts[5])),
            "confidence": float(parts[6]),
        }
        
        return sanitize_telemetry_data(row)
        
    except (ValueError, IndexError) as e:
        logger.error(f"CSV parsing error: {e}")
        return None


# ============================================================================
# ADVANCED SAFETY FEATURES INTEGRATION (Global Instances)
# ============================================================================
# These enable production-grade safety features across the system

try:
    from safety_features import (
        RiskHysteresisFilter,
        SensorFaultDetector,
        VelocitySanityFilter,
        MLConfidenceFusion,
        DatasetAutoLabeller,
    )
    
    # Initialize safety feature managers
    hysteresis_filter = RiskHysteresisFilter(deadband_sec=0.3)
    fault_detector = SensorFaultDetector(stuck_threshold=5)
    velocity_filter = VelocitySanityFilter()
    ml_fusion = MLConfidenceFusion()
    auto_labeller = DatasetAutoLabeller()
    
    SAFETY_FEATURES_ENABLED = True
    logger.info("Advanced safety features initialized")
    
except ImportError:
    SAFETY_FEATURES_ENABLED = False
    logger.warning("Safety features module not found - advanced features disabled")
