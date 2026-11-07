"""Train the host Random Forest and firmware threshold decision tree."""

import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.tree import DecisionTreeClassifier
import joblib

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from ml.training.split import (  # noqa: E402
    FEATURE_COLUMNS,
    TARGET_COLUMN,
    scenario_train_test_indices,
)
from src.config import DATASET_DIR, MODEL_PATH  # noqa: E402

CSV_PATH = DATASET_DIR / "synthetic_ttc_validation.csv"
HEADER_PATH = BASE_DIR / "firmware" / "ml_classifier" / "ml_classifier.h"
TARGET_NAMES = ["SAFE", "WARNING", "CRITICAL"]


def _print_test_report(name: str, y_true, y_pred) -> None:
    """Print held-out class metrics with labels and critical false-alarm rate."""
    print(f"\n{name} held-out test report:")
    print(
        classification_report(
            y_true,
            y_pred,
            labels=[0, 1, 2],
            target_names=TARGET_NAMES,
            zero_division=0,
        )
    )
    matrix = confusion_matrix(y_true, y_pred, labels=[0, 1, 2])
    negatives = matrix[0].sum() + matrix[1].sum()
    false_alarm_rate = (
        float(matrix[0, 2] + matrix[1, 2]) / negatives if negatives else 0.0
    )
    critical_recall = float(matrix[2, 2]) / matrix[2].sum() if matrix[2].sum() else 0.0
    print(
        f"accuracy={accuracy_score(y_true, y_pred):.4f}, "
        f"critical_recall={critical_recall:.4f}, "
        f"critical_false_alarm_rate={false_alarm_rate:.4f}"
    )


def _tree_to_c(tree: DecisionTreeClassifier, feature_names: list[str]) -> str:
    """
    Generate C++ code representation of decision tree classifier.

    Converts a trained scikit-learn DecisionTreeClassifier into executable C++ code
    suitable for deployment on embedded systems (ESP32). The generated code is a
    nested if-else structure that mirrors the tree's decision nodes.

    The output is a complete C++ header file containing an inline function
    'classifyRiskML' that accepts feature values and returns a risk class integer.

    Args:
        tree: Trained scikit-learn DecisionTreeClassifier with learned decision rules
        feature_names: List of feature column names in the same order as training data.
                      Expected: ['ttc_basic', 'ttc_ext', 'v_host', 'v_closing',
                                'a_decel', 'road_flag']

    Returns:
        String containing complete C++ header file code that implements the decision
        tree as a series of nested if-else statements. Each leaf node returns a risk
        class integer (0=SAFE, 1=WARNING, 2=CRITICAL).

    Example:
        >>> dt = DecisionTreeClassifier(max_depth=4)
        >>> dt.fit(X_train, y_train)
        >>> cpp_code = _tree_to_c(dt, ['ttc_basic', 'ttc_ext', 'v_host'])
        >>> # cpp_code contains: inline int classifyRiskML(...) { if (...) ... }
    """
    tree_ = tree.tree_
    feature_name = [
        feature_names[i] if i != -2 else "undefined!" for i in tree_.feature
    ]

    header = """#pragma once

// ml_classifier.h
// Auto-generated threshold decision tree from train_model.py.
// Do not manually modify. Replace via `python ml/training/train_model.py`.

/**
 * Exact function signature required by the firmware pipeline.
 * Features:
 *   - ttc_basic (s)
 *   - ttc_ext (s)
 *   - v_host (m/s)
 *   - v_closing (m/s)
 *   - a_decel (m/s^2)
 *   - road_flag (0=dry, 1=wet, 2=gravel, 3=ice)
 */
inline int classifyRiskML(float ttc_basic, float ttc_ext, float v_host, float v_closing, float a_decel, float road_flag) {
"""

    code = [header]

    def uniform_class(node: int):
        """Return the leaf class when every path below this node agrees."""
        if tree_.feature[node] == -2:
            return int(np.argmax(tree_.value[node][0]))
        left_class = uniform_class(tree_.children_left[node])
        right_class = uniform_class(tree_.children_right[node])
        if left_class is not None and left_class == right_class:
            return left_class
        return None

    def recurse(node: int, depth: int) -> None:
        """Emit only thresholds that can change the predicted class."""
        indent = "    " * depth
        cls = uniform_class(node)
        if cls is not None:
            code.append("{}return {}; // Class {}".format(indent, cls, cls))
            return

        name = feature_name[node]
        threshold = tree_.threshold[node]
        code.append("{}if ({} <= {:.3f}f) {{".format(indent, name, threshold))
        recurse(tree_.children_left[node], depth + 1)
        code.append("{}}} else {{".format(indent))
        recurse(tree_.children_right[node], depth + 1)
        code.append("{}}}".format(indent))

    recurse(0, 1)

    code.append("    return 0;\n}")
    return "\n".join(code)


def main() -> None:
    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found at {CSV_PATH}. "
            "Run `python src/synthetic_validation_dataset.py` first."
        )

    data = pd.read_csv(CSV_PATH)
    data = data.dropna(subset=FEATURE_COLUMNS + [TARGET_COLUMN, "scenario"])
    train_indices, test_indices = scenario_train_test_indices(data)
    train = data.iloc[train_indices]
    test = data.iloc[test_indices]
    X_train = train[FEATURE_COLUMNS]
    y_train = train[TARGET_COLUMN].astype(int)
    X_test = test[FEATURE_COLUMNS]
    y_test = test[TARGET_COLUMN].astype(int)

    print(f"Dataset rows: {len(data)}")
    print(f"Train rows: {len(train)}; scenarios: {sorted(train['scenario'].unique())}")
    print(f"Test rows: {len(test)}; scenarios: {sorted(test['scenario'].unique())}")

    rf = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
    rf.fit(X_train, y_train)

    os.makedirs(MODEL_PATH.parent, exist_ok=True)
    joblib.dump(rf, MODEL_PATH)
    print(f"\nSaved trained Random Forest to {MODEL_PATH}")
    _print_test_report("Random Forest", y_test, rf.predict(X_test))

    print("\nTraining threshold decision tree for firmware export...")
    dt = DecisionTreeClassifier(max_depth=4, min_samples_leaf=5, random_state=42)
    dt.fit(X_train, y_train)
    _print_test_report("Firmware threshold decision tree", y_test, dt.predict(X_test))

    cpp_code = _tree_to_c(dt, FEATURE_COLUMNS)

    os.makedirs(HEADER_PATH.parent, exist_ok=True)
    HEADER_PATH.write_text(cpp_code, encoding="utf-8")
    print(f"Exported threshold decision tree to {HEADER_PATH}")


if __name__ == "__main__":
    main()
