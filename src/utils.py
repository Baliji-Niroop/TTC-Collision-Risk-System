"""
System utilities — directory checks, health reports, environment validation.
"""

from datetime import datetime

from config import DATA_PATH, LOG_DIR, LOGGING_CONFIG
from logger import get_logger

logger = get_logger(__name__)


def ensure_directories():
    """Ensure all required directories exist."""
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        logger.info("Directory structure verified")
        return True
    except Exception as e:
        logger.error(f"Failed to create directories: {e}")
        return False


def clear_live_data():
    """Clear the live data file."""
    try:
        DATA_PATH.write_text("")
        logger.info("Live data file cleared")
        return True
    except Exception as e:
        logger.error(f"Failed to clear live data: {e}")
        return False


def export_logs_summary():
    """Create a summary of recent log entries."""
    log_file = LOGGING_CONFIG["log_file"]
    if not log_file.exists():
        return {"status": "no logs"}

    try:
        lines = log_file.read_text().splitlines()
        levels = {"DEBUG": 0, "INFO": 0, "WARNING": 0, "ERROR": 0, "CRITICAL": 0}
        for line in lines:
            for level in levels:
                if f" - {level} - " in line:
                    levels[level] += 1

        return {
            "total_lines": len(lines),
            "by_level": levels,
            "last_entry": lines[-1] if lines else None,
            "file": str(log_file),
        }
    except Exception as e:
        logger.error(f"Error creating log summary: {e}")
        return {"status": "error", "message": str(e)}


def format_telemetry(row: dict) -> str:
    """Format telemetry data for display."""
    try:
        ttc = row.get("ttc_basic", 0)
        distance = row.get("distance_cm", 0) / 100
        speed = row.get("speed_kmh", 0)
        confidence = row.get("confidence", 0) * 100

        status = "healthy"
        if row.get("anomaly_flag"):
            status = "[ANOMALY]"
        elif ttc < 1.5:
            status = "[CRITICAL]"
        elif ttc < 3.0:
            status = "[WARNING]"

        return (
            f"Status: {status} | "
            f"TTC: {ttc:.2f}s | "
            f"Distance: {distance:.2f}m | "
            f"Speed: {speed:.1f} km/h | "
            f"Confidence: {confidence:.0f}%"
        )
    except Exception as e:
        return f"Error formatting: {e}"


def get_system_health() -> dict:
    """Check overall system health."""
    health = {
        "timestamp": datetime.now().isoformat(),
        "components": {
            "directories": ensure_directories(),
            "logs": bool(LOGGING_CONFIG["log_file"].exists()),
            "live_data": bool(DATA_PATH.exists()),
        },
        "status": "operational",
    }

    if not all(health["components"].values()):
        health["status"] = "degraded"

    return health


def generate_health_report() -> str:
    """Generate a human-readable health report."""
    health = get_system_health()

    report = "=" * 60 + "\n"
    report += "TTC SYSTEM HEALTH REPORT\n"
    report += "=" * 60 + "\n"
    report += f"Timestamp: {health['timestamp']}\n"
    report += f"Status: {health['status'].upper()}\n\n"
    report += "Components:\n"

    for component, status in health["components"].items():
        status_str = "OK" if status else "FAIL"
        report += f"  {component}: {status_str}\n"

    report += "\n" + "=" * 60 + "\n"
    return report


def reset_system():
    """Reset the system to initial state."""
    try:
        clear_live_data()
        ensure_directories()
        logger.info("System reset completed")
        return True
    except Exception as e:
        logger.error(f"Error during reset: {e}")
        return False


def validate_environment() -> dict:
    """Validate that all required modules and dependencies are available."""
    results = {}

    required_modules = [
        ("pandas", "pandas"),
        ("numpy", "numpy"),
        ("streamlit", "streamlit"),
        ("scikit-learn", "sklearn"),
        ("joblib", "joblib"),
        ("pyserial", "serial"),
    ]

    for display_name, import_name in required_modules:
        try:
            __import__(import_name)
            results[display_name] = True
        except ImportError:
            results[display_name] = False
            logger.warning(f"Missing module: {display_name}")

    results["directories"] = ensure_directories()

    try:
        import config  # noqa: F401

        results["config"] = True
    except ImportError:
        results["config"] = False

    return results


def print_environment_check():
    """Print environment validation results."""
    results = validate_environment()

    print("\n" + "=" * 60)
    print("ENVIRONMENT VALIDATION")
    print("=" * 60)

    for key, status in results.items():
        status_str = "OK" if status else "FAIL"
        print(f"{status_str} {key}")

    all_ok = all(results.values())
    print("=" * 60)
    print(f"Overall: {'READY' if all_ok else 'ISSUES FOUND'}")
    print("=" * 60 + "\n")

    return all_ok


def performance_benchmark():
    """Run performance benchmarks on critical functions."""
    import time

    from validators import detect_anomalies, validate_csv_line

    results = {}

    test_line = "1000,2000.5,50.0,2.5,2.4,1,0.92"
    start = time.perf_counter()
    for _ in range(1000):
        validate_csv_line(test_line)
    results["csv_parsing_1000_calls"] = round(time.perf_counter() - start, 4)

    test_data = [{"ttc_basic": 1.5 + 0.1 * i, "confidence": 0.8} for i in range(100)]
    start = time.perf_counter()
    detect_anomalies(test_data)
    results["anomaly_detection_100_rows"] = round(time.perf_counter() - start, 4)

    return results


def quick_health_check():
    """Quick health check."""
    return print_environment_check()


def show_health_report():
    """Show detailed health report."""
    print(generate_health_report())
