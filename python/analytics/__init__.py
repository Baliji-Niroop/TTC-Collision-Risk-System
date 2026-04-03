"""
analytics.py
Session analytics, TTC statistics, trend detection, and risk insights.
"""

from typing import Dict, Any
import statistics
from logger import get_logger

logger = get_logger(__name__)


class SessionAnalytics:
    """Analyzes TTC session data for insights and trends."""

    def __init__(self):
        self.events = []
        self.start_time = None

    def add_event(self, event_data: Dict[str, Any]):
        """Add an event to the session."""
        self.events.append(event_data)

    def get_risk_distribution(self) -> Dict[str, float]:
        """
        Calculate percentage time in each risk zone.

        Returns:
            Dict with SAFE, WARNING, CRITICAL percentages
        """
        if not self.events:
            return {"SAFE": 0, "WARNING": 0, "CRITICAL": 0}

        risk_counts = {"SAFE": 0, "WARNING": 0, "CRITICAL": 0}
        risk_labels = {0: "SAFE", 1: "WARNING", 2: "CRITICAL"}

        for event in self.events:
            risk = event.get("risk_class", event.get("risk", 0))
            risk_label = risk_labels.get(risk, "SAFE")
            risk_counts[risk_label] += 1

        total = len(self.events)
        return {k: round(v / total * 100, 1) for k, v in risk_counts.items()}

    def get_ttc_statistics(self) -> Dict[str, float]:
        """
        Calculate TTC statistics (min, max, mean, median, stdev).

        Returns:
            Dictionary with statistical measures
        """
        ttc_values = [e.get("ttc_basic", 0) for e in self.events if e.get("ttc_basic", 0) < 99.0]

        if not ttc_values:
            return {"min": 0, "max": 0, "mean": 0, "median": 0, "stdev": 0}

        try:
            return {
                "min": round(min(ttc_values), 2),
                "max": round(max(ttc_values), 2),
                "mean": round(statistics.mean(ttc_values), 2),
                "median": round(statistics.median(ttc_values), 2),
                "stdev": round(statistics.stdev(ttc_values) if len(ttc_values) > 1 else 0, 2),
            }
        except Exception as e:
            logger.error(f"Error calculating TTC statistics: {e}")
            return {"min": 0, "max": 0, "mean": 0, "median": 0, "stdev": 0}

    def get_trend_direction(self, window: int = 5) -> str:
        """
        Determine if TTC is trending up (safer) or down (more dangerous).

        Args:
            window: Number of recent events to analyze

        Returns:
            "improving", "degrading", or "stable"
        """
        if len(self.events) < window:
            return "insufficient_data"

        recent = self.events[-window:]
        ttc_vals = [e.get("ttc_basic", 0) for e in recent if e.get("ttc_basic", 0) < 99.0]

        if len(ttc_vals) < 2:
            return "stable"

        mid = len(ttc_vals) // 2
        first_half_mean = statistics.mean(ttc_vals[:mid]) if mid > 0 else ttc_vals[0]
        second_half_mean = statistics.mean(ttc_vals[mid:]) if len(ttc_vals) > mid else ttc_vals[mid]

        change = second_half_mean - first_half_mean
        threshold = 0.2

        if change > threshold:
            return "improving"
        if change < -threshold:
            return "degrading"
        return "stable"

    def predict_ttc_at_time(self, seconds_ahead: int = 5) -> float:
        """
        Simple linear extrapolation of TTC trend.

        Args:
            seconds_ahead: How many seconds to predict ahead

        Returns:
            Predicted TTC value
        """
        window = min(10, len(self.events))
        if window < 2:
            return 99.0

        recent = self.events[-window:]
        ttc_vals = [e.get("ttc_basic", 0) for e in recent if e.get("ttc_basic", 0) < 99.0]

        if len(ttc_vals) < 2:
            return ttc_vals[0] if ttc_vals else 99.0

        try:
            n = len(ttc_vals)
            x_vals = list(range(n))
            x_mean = statistics.mean(x_vals)
            y_mean = statistics.mean(ttc_vals)

            numerator = sum((x_vals[i] - x_mean) * (ttc_vals[i] - y_mean) for i in range(n))
            denominator = sum((x_vals[i] - x_mean) ** 2 for i in range(n))

            if denominator == 0:
                return ttc_vals[-1]

            slope = numerator / denominator
            intercept = y_mean - slope * x_mean
            predicted = slope * (n + seconds_ahead) + intercept
            return max(0, round(predicted, 2))
        except Exception as e:
            logger.error(f"Error in TTC prediction: {e}")
            return ttc_vals[-1] if ttc_vals else 99.0

    def get_critical_events_info(self) -> Dict[str, Any]:
        """
        Analyze CRITICAL risk events.

        Returns:
            Dictionary with CRITICAL event statistics
        """
        critical_events = [e for e in self.events if e.get("risk_class", e.get("risk", 0)) == 2]

        if not critical_events:
            return {
                "count": 0,
                "first_occurrence": None,
                "last_occurrence": None,
                "avg_duration": 0,
                "severity_avg": 0,
            }

        ttc_values = [e.get("ttc_basic", 0) for e in critical_events]

        return {
            "count": len(critical_events),
            "first_occurrence": critical_events[0].get("timestamp", None),
            "last_occurrence": critical_events[-1].get("timestamp", None),
            "min_ttc": min(ttc_values),
            "max_ttc": max(ttc_values),
            "avg_ttc": round(statistics.mean(ttc_values), 2),
            "avg_confidence": round(statistics.mean([e.get("confidence", 0) for e in critical_events]), 2),
        }


def calculate_collision_probability(ttc: float, confidence: float = 1.0) -> float:
    """Estimate collision probability based on TTC and model confidence."""
    if ttc <= 0.5:
        prob = 0.95
    elif ttc <= 1.0:
        prob = 0.75
    elif ttc <= 1.5:
        prob = 0.50
    elif ttc <= 2.0:
        prob = 0.30
    elif ttc <= 3.0:
        prob = 0.10
    else:
        prob = 0.01

    return prob * confidence


def recommend_action(risk_class: int, ttc: float, confidence: float = 1.0) -> str:
    """Recommend driver action based on risk assessment."""
    if risk_class == 2:
        if ttc < 0.75:
            return "[EMERGENCY] BRAKE - COLLISION IMMINENT"
        return "[CRITICAL] APPLY HARD BRAKE"

    if risk_class == 1:
        if ttc < 1.0:
            return "[WARNING] BEGIN EMERGENCY STOP"
        return "[WARNING] REDUCE SPEED"

    if confidence < 0.7:
        return "[ALERT] Low model confidence"
    return "SAFE - CONTINUE"
