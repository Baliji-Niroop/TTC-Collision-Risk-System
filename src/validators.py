"""
Data Validation Module

Checks incoming sensor data for quality and correctness.
Detects problems like out-of-range values, anomalies, and formatting errors.
Automatically fixes minor issues when possible.
"""

from typing import Optional, Dict, Any

try:
    from config import ANOMALY_CONFIG, SERIAL_CONFIG, TELEMETRY_FIELDS
    from logger import get_logger
    from telemetry_schema import parse_packet
except ImportError:
    from src.config import ANOMALY_CONFIG, SERIAL_CONFIG, TELEMETRY_FIELDS
    from src.logger import get_logger
    from src.telemetry_schema import parse_packet

import statistics

logger = get_logger(__name__)

LEGACY_ALIAS_FIELDS = {"risk_phys", "v_closing_kmh", "ttc_basic_s", "speed_alias"}


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

    parts = [part.strip() for part in line.split(",")]
    if len(parts) != SERIAL_CONFIG["expected_fields"]:
        logger.warning(
            f"Invalid field count: expected {SERIAL_CONFIG['expected_fields']}, got {len(parts)}"
        )
        return False

    # Reject header-like lines and legacy alias tokens in strict mode.
    joined = ",".join(parts)
    if any(alias in joined for alias in LEGACY_ALIAS_FIELDS):
        logger.warning("Legacy alias field detected in telemetry line")
        return False

    if any(any(ch.isalpha() for ch in part) for part in parts):
        logger.warning("Non-numeric token detected in telemetry packet")
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
        # Canonical-only schema enforcement.
        expected = set(TELEMETRY_FIELDS)
        actual = set(row.keys())
        if actual != expected:
            missing = sorted(expected - actual)
            extra = sorted(actual - expected)
            logger.warning(f"Schema mismatch. Missing={missing}, extra={extra}")
            return None

        # Validate ranges
        timestamp_ms = float(row["timestamp_ms"])
        distance = float(row["distance_cm"])
        speed = float(row["speed_kmh"])
        ttc_basic = float(row["ttc_basic"])
        confidence = float(row["confidence"])
        risk_class = int(row["risk_class"])

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

        if timestamp_ms < 0:
            logger.warning(f"Negative timestamp detected: {timestamp_ms}")
            return None

        if risk_class not in (0, 1, 2):
            logger.warning(f"Invalid risk class: {risk_class}")
            return None

        row["anomaly_flag"] = False
        row["risk_class"] = risk_class
        return row

    except (ValueError, TypeError) as e:
        logger.error(f"Data type error during validation: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}", exc_info=True)
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
    if not data_buffer:
        return {"anomalies": [], "anomaly_count": 0}

    # Confidence-drop checks require at least two samples.
    if len(data_buffer) < 2:
        return {"anomalies": [], "anomaly_count": 0}

    anomalies = []

    try:
        # Extract TTC values
        ttc_values = [
            d.get("ttc_basic", 0) for d in data_buffer if d.get("ttc_basic", 0) < 99.0
        ]

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
                            anomalies.append(
                                {
                                    "index": i,
                                    "type": "ttc_outlier",
                                    "value": ttc,
                                    "z_score": z_score,
                                }
                            )

        # Check for sudden confidence drops
        if len(data_buffer) >= 2:
            for i in range(1, len(data_buffer)):
                prev_conf = data_buffer[i - 1].get("confidence", 1.0)
                curr_conf = data_buffer[i].get("confidence", 1.0)
                drop = prev_conf - curr_conf

                if drop > ANOMALY_CONFIG["max_confidence_drop"]:
                    anomalies.append(
                        {"index": i, "type": "confidence_drop", "drop": drop}
                    )

        if anomalies:
            logger.warning(f"Detected {len(anomalies)} anomalies in buffer")

        return {
            "anomalies": anomalies,
            "mean_ttc": mean_ttc if len(ttc_values) >= 3 else None,
            "anomaly_count": len(anomalies),
        }

    except (ValueError, ZeroDivisionError) as e:
        logger.error(f"Calculation error during anomaly detection: {e}")
        return {"anomalies": [], "error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error during anomaly detection: {e}", exc_info=True)
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
        row = parse_packet(line)
        if row is None:
            return None

        return sanitize_telemetry_data(row)

    except ValueError as e:
        logger.error(f"CSV parsing error - invalid data format: {e}")
        return None
    except IndexError as e:
        logger.error(f"CSV parsing error - field index out of range: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error parsing CSV line: {e}", exc_info=True)
        return None


# Safety features bootstrap — instantiate global instances if available

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

except ImportError as e:
    SAFETY_FEATURES_ENABLED = False
    logger.warning(
        f"Safety features module not found - advanced features disabled: {e}"
    )
except Exception as e:
    SAFETY_FEATURES_ENABLED = False
    logger.error(f"Unexpected error initializing safety features: {e}", exc_info=True)
