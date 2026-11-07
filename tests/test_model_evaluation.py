"""Tests for scenario-level model training and evaluation."""

from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from ml.inference import _feature_frame
from ml.training.split import (
    TARGET_COLUMN,
    scenario_train_test_indices,
)
from ml.training.train_model import _tree_to_c
from src.config import DATASET_DIR
from validation import evaluate_synthetic


def test_scenario_split_keeps_scenarios_disjoint():
    dataset = pd.read_csv(DATASET_DIR / "synthetic_ttc_validation.csv")
    train_indices, test_indices = scenario_train_test_indices(dataset)
    train_scenarios = set(dataset.iloc[train_indices]["scenario"])
    test_scenarios = set(dataset.iloc[test_indices]["scenario"])

    assert train_scenarios.isdisjoint(test_scenarios)
    assert set(dataset.iloc[train_indices][TARGET_COLUMN]) == {0, 1, 2}
    assert set(dataset.iloc[test_indices][TARGET_COLUMN]) == {0, 1, 2}


def test_evaluation_fails_when_model_is_missing(monkeypatch):
    monkeypatch.setattr(evaluate_synthetic, "load_model", lambda: None)

    with pytest.raises(RuntimeError, match="Run `python ml/training/train_model.py`"):
        evaluate_synthetic.main()


def test_host_speed_feature_uses_meters_per_second():
    class Model:
        feature_names_in_ = ["v_host"]

    features = _feature_frame({"speed_kmh": 36.0}, Model())

    assert features.loc[0, "v_host"] == 10.0


def test_firmware_tree_export_collapses_identical_branches():
    tree = SimpleNamespace(
        tree_=SimpleNamespace(
            feature=np.array([0, -2, -2]),
            children_left=np.array([1, -1, -1]),
            children_right=np.array([2, -1, -1]),
            threshold=np.array([1.5, -2.0, -2.0]),
            value=np.array(
                [
                    [[2.0, 0.0, 0.0]],
                    [[1.0, 0.0, 0.0]],
                    [[1.0, 0.0, 0.0]],
                ]
            ),
        )
    )

    exported = _tree_to_c(tree, ["ttc_basic"])

    assert "if (" not in exported
    assert "return 0; // Class 0" in exported
