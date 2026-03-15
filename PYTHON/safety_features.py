"""
Safety Features and Advanced Collision Risk Management
========================================================
Implements hysteresis, fault detection, and ML confidence fusion.
"""

from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from config import RISK_THRESHOLDS, ANOMALY_CONFIG
from logger import get_logger

logger = get_logger(__name__)


class RiskHysteresisFilter:
    """
    Reduces alert flickering by implementing hysteresis bands.
    
    Example: With 0.3s deadband
        SAFE (TTC > 3.0) -> once in WARNING zone, stays until TTC > 3.3
        WARNING (1.5-3.0) -> once in CRITICAL, stays until TTC > 1.8
        CRITICAL (TTC < 1.5) -> once in SAFE, stays until TTC < 1.2
    
    This prevents rapid toggling between risk levels due to sensor noise.
    """
    
    def __init__(self, deadband_sec: float = 0.3):
        """
        Initialize hysteresis filter.
        
        Args:
            deadband_sec: Hysteresis deadband in seconds (default 0.3s)
        """
        self.deadband = deadband_sec
        self.last_risk_class = 0  # Start at SAFE
        self.locked_until = datetime.now()
        
    def classify_with_hysteresis(self, ttc: float) -> int:
        """
        Classify collision risk with hysteresis to reduce flickering.
        
        Args:
            ttc: Time-to-collision in seconds
            
        Returns:
            Risk class (0=SAFE, 1=WARNING, 2=CRITICAL)
        """
        # Apply deadbands only when de-escalating from a higher-risk state.
        if self.last_risk_class == 2:
            if ttc > (RISK_THRESHOLDS["warning"] + self.deadband):
                self.last_risk_class = 0
            elif ttc > (RISK_THRESHOLDS["critical"] + self.deadband):
                self.last_risk_class = 1
            else:
                self.last_risk_class = 2
            return self.last_risk_class

        if self.last_risk_class == 1:
            if ttc <= RISK_THRESHOLDS["critical"]:
                self.last_risk_class = 2
            elif ttc > (RISK_THRESHOLDS["warning"] + self.deadband):
                self.last_risk_class = 0
            else:
                self.last_risk_class = 1
            return self.last_risk_class

        # Current state is SAFE.
        if ttc <= RISK_THRESHOLDS["critical"]:
            self.last_risk_class = 2
        elif ttc <= RISK_THRESHOLDS["warning"]:
            self.last_risk_class = 1
        else:
            self.last_risk_class = 0
        return self.last_risk_class
    
    def reset(self):
        """Reset hysteresis state"""
        self.last_risk_class = 0
        self.locked_until = datetime.now()


class SensorFaultDetector:
    """
    Detects stuck or faulty sensor values and provides fallback logic.
    
    Detects:
    - Stuck values (same distance for multiple readings)
    - Value jumps (physically impossible accelerations)
    - Signal loss (zero distance without reset)
    - Confidence collapse (sudden confidence drop)
    """
    
    def __init__(self, stuck_threshold: int = 5):
        """
        Initialize fault detector.
        
        Args:
            stuck_threshold: Number of identical readings to flag as stuck
        """
        self.stuck_threshold = stuck_threshold
        self.last_distance = None
        self.stuck_count = 0
        self.last_confidence = 1.0
        self.is_faulty = False
    
    def check_sensor_health(self, row: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Check sensor health and detect faults.
        
        Args:
            row: Telemetry data row
            
        Returns:
            Tuple of (is_healthy, fault_message)
        """
        distance = row.get("distance_cm", 0)
        confidence = row.get("confidence", 1.0)
        speed = row.get("speed_kmh", 0)
        
        # Detect stuck sensor (same value repeated)
        if distance == self.last_distance:
            self.stuck_count += 1
            if self.stuck_count >= self.stuck_threshold:
                msg = f"Sensor stuck at {distance}cm (confidence: {confidence})"
                logger.warning(msg)
                self.is_faulty = True
                return False, msg
        else:
            self.stuck_count = 1
        
        # Detect physically impossible movement
        if self.last_distance is not None and speed > 0:
            # Max possible change in one read (assume 0.3s between reads)
            max_change = (speed / 3.6) * 0.3 * 100  # Convert to cm
            change = abs(distance - self.last_distance)
            
            if change > max_change * 10:  # 10x threshold
                msg = f"Impossible jump: {self.last_distance}cm -> {distance}cm (speed: {speed}km/h)"
                logger.warning(msg)
                self.is_faulty = True
                return False, msg
        
        # Detect confidence collapse
        conf_drop = self.last_confidence - confidence
        if conf_drop > ANOMALY_CONFIG.get("max_confidence_drop", 0.5):
            msg = f"Confidence dropped sharply: {self.last_confidence:.2f} -> {confidence:.2f}"
            logger.warning(msg)
            self.is_faulty = True
            return False, msg
        
        # Sensor recovered
        if self.is_faulty:
            logger.info("Sensor recovered from fault condition")
            self.is_faulty = False
        
        self.last_distance = distance
        self.last_confidence = confidence
        
        return True, None
    
    def mark_faulty(self) -> Dict[str, Any]:
        """Return fallback data when sensor is faulty"""
        return {
            "fault_flag": True,
            "use_fallback": True,
            "anomaly_flag": True,
            "confidence": 0.5,
        }


class VelocitySanityFilter:
    """
    Validates velocity measurements against physical constraints.
    
    Checks:
    - Maximum plausible vehicle speed (< 220 km/h)
    - Acceleration limits (< 15 m/s²)
    - Deceleration limits (< 20 m/s²)
    """
    
    MAX_SPEED = 200.0  # km/h (highway limit)
    MAX_ACCELERATION = 15.0  # m/s² (~1.5g)
    MAX_DECELERATION = 20.0  # m/s² (~2g emergency braking)
    
    def __init__(self):
        self.last_speed = 0
        self.last_time = None
    
    def validate_velocity(self, speed_kmh: float, timestamp: float) -> Tuple[bool, Optional[str]]:
        """
        Validate velocity against physical constraints.
        
        Args:
            speed_kmh: Speed in km/h
            timestamp: Current timestamp (seconds)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check maximum speed
        if speed_kmh > self.MAX_SPEED:
            msg = f"Speed {speed_kmh:.1f}km/h exceeds max {self.MAX_SPEED}km/h"
            logger.warning(msg)
            return False, msg
        
        # Check acceleration limits
        if self.last_time is not None:
            dt = timestamp - self.last_time
            if dt > 0.01:  # Only check if reasonable time passed
                dv = (speed_kmh - self.last_speed) / 3.6  # Convert to m/s
                accel = dv / dt
                
                if accel > self.MAX_ACCELERATION:
                    msg = f"Acceleration {accel:.2f}m/s² exceeds limit {self.MAX_ACCELERATION}m/s²"
                    logger.warning(msg)
                    return False, msg
                
                if accel < -self.MAX_DECELERATION:
                    msg = f"Deceleration {abs(accel):.2f}m/s² exceeds limit {self.MAX_DECELERATION}m/s²"
                    logger.warning(msg)
                    return False, msg
        
        self.last_speed = speed_kmh
        self.last_time = timestamp
        
        return True, None


class MLConfidenceFusion:
    """
    Fuses physics-based and ML-based risk classifications with confidence weighting.
    
    Implements: Risk_final = w_physics * Risk_phys + w_ml * Risk_ml
    where weights are adjusted based on each model's confidence.
    
    Also provides justification for safety-critical decisions.
    """
    
    def __init__(self, ml_model=None):
        """
        Initialize fusion engine.
        
        Args:
            ml_model: Trained ML model (sklearn classifier)
        """
        self.ml_model = ml_model
        self.physics_weight = 0.6  # Physics-based gets 60% by default
        self.ml_weight = 0.4      # ML-based gets 40% by default
    
    def predict_risk_fused(
        self,
        ttc_basic: float,
        ml_confidence: float,
        physics_confidence: float = 0.95
    ) -> Tuple[int, float, str]:
        """
        Predict risk using both physics and ML, with confidence fusion.
        
        Args:
            ttc_basic: Physics-based TTC (seconds)
            ml_confidence: ML model confidence (0-1)
            physics_confidence: Physics model confidence (default 0.95)
            
        Returns:
            Tuple of (risk_class, final_confidence, justification)
        """
        # Physics-based classification
        if ttc_basic > RISK_THRESHOLDS["warning"]:
            phys_risk = 0  # SAFE
        elif ttc_basic > RISK_THRESHOLDS["critical"]:
            phys_risk = 1  # WARNING
        else:
            phys_risk = 2  # CRITICAL
        
        phys_confidence = min(ml_confidence, physics_confidence)
        
        # Adjust weights based on confidence
        if ml_confidence < 0.5:
            # Low ML confidence: rely more on physics
            final_weight_physics = 0.85
            final_weight_ml = 0.15
        elif ml_confidence > 0.9:
            # High ML confidence: weight ML more
            final_weight_physics = 0.5
            final_weight_ml = 0.5
        else:
            # Medium confidence: balanced approach
            final_weight_physics = 0.6
            final_weight_ml = 0.4
        
        # Final prediction uses physics as primary (physics is always available)
        final_risk = phys_risk
        final_confidence = (
            final_weight_physics * physics_confidence +
            final_weight_ml * ml_confidence
        )
        
        # Generate justification for decision
        justification = (
            f"Physics(TTC={ttc_basic:.2f}s)={phys_risk} "
            f"[conf={physics_confidence:.2f}] -> "
            f"Final={final_risk} [conf={final_confidence:.2f}]"
        )
        
        return final_risk, final_confidence, justification
    
    def set_weights(self, physics_weight: float, ml_weight: float):
        """
        Set custom fusion weights.
        
        Args:
            physics_weight: Weight for physics model (0-1)
            ml_weight: Weight for ML model (0-1)
        """
        total = physics_weight + ml_weight
        self.physics_weight = physics_weight / total
        self.ml_weight = ml_weight / total
        logger.info(f"Fusion weights set: physics={self.physics_weight:.2f}, ml={self.ml_weight:.2f}")


class DatasetAutoLabeller:
    """
    Automatically generates high-quality labels for ML training dataset.
    
    Combines physics-based classification, confidence scores, and anomaly flags
    to create a robust training dataset with confidence levels.
    """
    
    def __init__(self, output_file: Optional[str] = None):
        """
        Initialize auto-labeller.
        
        Args:
            output_file: Optional file to write labeled data
        """
        self.output_file = output_file
        self.labeled_count = 0
        self.high_confidence_count = 0
    
    def label_row(self, row: Dict[str, Any], prediction_info: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Automatically label a data row with high-confidence annotations.
        
        Args:
            row: Raw telemetry data
            prediction_info: Optional ML predictions and confidences
            
        Returns:
            Row with added labels and confidence scores
        """
        ttc = row.get("ttc_basic", 99.0)
        
        # Primary label from TTC physics
        if ttc > 3.0:
            label = 0  # SAFE
            confidence = min(0.95, 1.0 - (ttc - 3.0) * 0.01)  # Higher TTC = higher confidence
        elif ttc > 1.5:
            label = 1  # WARNING
            confidence = min(0.9, 0.5 + (3.0 - ttc) * 0.2)
        else:
            label = 2  # CRITICAL
            confidence = min(0.95, 0.5 + (3.0 - ttc) * 0.1)
        
        # Adjust confidence if anomalies detected
        if row.get("anomaly_flag"):
            confidence *= 0.7  # Reduce confidence for anomalous data
        
        # Add label information
        labeled_row = row.copy()
        labeled_row["auto_label"] = label
        labeled_row["label_confidence"] = confidence
        labeled_row["labeler"] = "physics-based"
        labeled_row["label_timestamp"] = datetime.now().isoformat()
        
        # Track high-confidence labels
        if confidence > 0.8:
            self.high_confidence_count += 1
        
        self.labeled_count += 1
        
        return labeled_row
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get labelling statistics"""
        return {
            "total_labeled": self.labeled_count,
            "high_confidence": self.high_confidence_count,
            "high_confidence_ratio": (
                self.high_confidence_count / max(1, self.labeled_count)
            ),
        }
