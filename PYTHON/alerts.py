"""
Alerting Module
===============
Manages alerts and notifications for critical events.
"""

from typing import Optional, Callable
from datetime import datetime
from config import ALERT_CONFIG, RISK_LABELS
from logger import get_logger

logger = get_logger(__name__)

# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ ALERT MANAGER
# ╚═══════════════════════════════════════════════════════════════════════════╝

class AlertManager:
    """Manages and throttles alerts."""
    
    def __init__(self):
        self.last_critical_alert_time = None
        self.last_warning_alert_time = None
        self.warning_count_since_alert = 0
        self.critical_count_since_alert = 0
        self.callbacks = []
    
    def register_callback(self, callback: Callable):
        """Register a callback to be called on alerts."""
        self.callbacks.append(callback)
    
    def trigger_alert(self, risk_class: int, row: dict) -> bool:
        """
        Trigger an alert if conditions are met.
        
        Args:
            risk_class: Risk class (0, 1, or 2)
            row: Telemetry row data
            
        Returns:
            True if alert was triggered, False if throttled
        """
        if not ALERT_CONFIG["enable_alerts"]:
            return False
        
        now = datetime.now()
        should_alert = False
        alert_msg = None
        
        try:
            if risk_class == 2:  # CRITICAL
                self.critical_count_since_alert += 1
                if self.critical_count_since_alert >= ALERT_CONFIG["critical_alert_every_n_events"]:
                    should_alert = True
                    alert_msg = f"[!!] CRITICAL COLLISION RISK - TTC: {row.get('ttc_basic', 'N/A'):.2f}s"
                    self.critical_count_since_alert = 0
                    self.last_critical_alert_time = now
                    
            elif risk_class == 1:  # WARNING
                self.warning_count_since_alert += 1
                if self.warning_count_since_alert >= ALERT_CONFIG["warning_alert_every_n_events"]:
                    should_alert = True
                    alert_msg = f"[!] WARNING - Approaching danger zone - TTC: {row.get('ttc_basic', 'N/A'):.2f}s"
                    self.warning_count_since_alert = 0
                    self.last_warning_alert_time = now
            
            # Check for extreme low TTC
            ttc = row.get("ttc_basic", 99.0)
            if ttc < ALERT_CONFIG["min_ttc_alert_threshold"]:
                should_alert = True
                alert_msg = f"[IMMINENT] COLLISION - TTC: {ttc:.2f}s - BRAKE IMMEDIATELY"
            
            if should_alert and alert_msg:
                self._dispatch_alert(alert_msg, risk_class, row)
                logger.warning(alert_msg)
                return True
                
        except Exception as e:
            logger.error(f"Error in alert trigger: {e}")
        
        return False
    
    def _dispatch_alert(self, message: str, risk_class: int, row: dict):
        """Dispatch alert to registered callbacks."""
        alert_data = {
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "risk_class": risk_class,
            "risk_label": RISK_LABELS.get(risk_class, "UNKNOWN"),
            "ttc": row.get("ttc_basic", None),
            "distance": row.get("distance_cm", None),
            "speed": row.get("speed_kmh", None),
        }
        
        for callback in self.callbacks:
            try:
                callback(alert_data)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")


# Global alert manager instance
_alert_manager = None

def get_alert_manager() -> AlertManager:
    """Get or create the global alert manager."""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager


def check_and_alert(risk_class: int, row: dict) -> bool:
    """Convenience function to check and trigger alerts."""
    manager = get_alert_manager()
    return manager.trigger_alert(risk_class, row)
