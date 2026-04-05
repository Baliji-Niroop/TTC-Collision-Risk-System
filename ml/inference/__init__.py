"""
ml_inference.py
Shared ML inference helpers used by the dashboard, validation pipeline,
and replay runner.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pandas as pd

from config import MODEL_PATH

FALLBACK_FEATURE_COLUMNS = ["ttc_basic", "ttc_ext", "v_host", "v_closing", "a_decel", "road_flag"]


@lru_cache(maxsize=1)
def load_model(model_path: Optional[str] = None):
    """Load the serialized classifier if it exists."""
    try:
        import joblib
    except ImportError:
        return None

    path = Path(model_path) if model_path else MODEL_PATH
    if not path.exists():
        return None

    try:
        return joblib.load(path)
    except Exception:
        return None


def _feature_frame(row: Dict[str, Any], model) -> pd.DataFrame:
    distance_m = float(row.get("distance_cm", 0.0)) / 100.0
    speed_kmh = float(row.get("speed_kmh", 0.0))
    ttc_basic = float(row.get("ttc_basic", 99.0))
    closing_vel = distance_m / max(ttc_basic, 0.1)
    a_decel = float(row.get("a_decel", 5.0))

    feature_map = {
        "ttc_basic": ttc_basic,
        "ttc_ext": float(row.get("ttc_ext", ttc_basic)),
        "v_host": speed_kmh,
        "v_closing": closing_vel,
        "a_decel": a_decel,
        "road_flag": float(row.get("road_flag", row.get("road", 0.0))),
    }

    if hasattr(model, "expected_features"):
        columns = list(model.expected_features)
    elif hasattr(model, "feature_names_in_"):
        columns = list(model.feature_names_in_)
    else:
        columns = FALLBACK_FEATURE_COLUMNS

    return pd.DataFrame([{column: feature_map.get(column, 0.0) for column in columns}], columns=columns)


def predict_risk(row: Dict[str, Any], model=None) -> int:
    """Predict a risk class or fall back to the provided physics class."""
    model = model or load_model()
    fallback = int(row.get("risk_class", 0))
    if model is None:
        return fallback

    try:
        features = _feature_frame(row, model)
        return int(model.predict(features)[0])
    except Exception:
        return fallback


def predict_risk_with_confidence(row: Dict[str, Any], model=None) -> Tuple[int, float]:
    """Return a predicted risk class and a confidence estimate."""
    model = model or load_model()
    fallback_class = int(row.get("risk_class", 0))
    fallback_confidence = float(row.get("confidence", 0.5))

    if model is None:
        return fallback_class, fallback_confidence

    try:
        features = _feature_frame(row, model)
        predicted = int(model.predict(features)[0])

        if hasattr(model, "predict_proba"):
            probabilities = model.predict_proba(features)[0]
            confidence = float(max(probabilities))
        elif hasattr(model, "decision_function"):
            confidence = 0.85
        else:
            confidence = fallback_confidence

        return predicted, max(0.0, min(1.0, confidence))
    except Exception:
        return fallback_class, fallback_confidence
