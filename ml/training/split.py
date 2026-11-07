"""Shared scenario-level split for model training and evaluation."""

from sklearn.model_selection import GroupShuffleSplit

FEATURE_COLUMNS = [
    "ttc_basic",
    "ttc_ext",
    "v_host",
    "v_closing",
    "a_decel",
    "road_flag",
]
TARGET_COLUMN = "ground_truth_risk_class"
TEST_SIZE = 0.33
RANDOM_STATE = 0
RISK_CLASSES = {0, 1, 2}


def scenario_train_test_indices(data):
    """Return row indices for reproducible, scenario-disjoint train/test splits."""
    required = {"scenario", TARGET_COLUMN, *FEATURE_COLUMNS}
    missing = required.difference(data.columns)
    if missing:
        raise ValueError(f"Dataset is missing required columns: {sorted(missing)}")
    if data["scenario"].isna().any():
        raise ValueError("Scenario names must not be empty.")

    splitter = GroupShuffleSplit(
        n_splits=1,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
    )
    train_indices, test_indices = next(
        splitter.split(data, groups=data["scenario"])
    )

    train_scenarios = set(data.iloc[train_indices]["scenario"])
    test_scenarios = set(data.iloc[test_indices]["scenario"])
    if train_scenarios.intersection(test_scenarios):
        raise RuntimeError("Scenario leakage detected between train and test splits.")

    for split_name, indices in (
        ("TRAIN", train_indices),
        ("TEST", test_indices),
    ):
        classes = set(data.iloc[indices][TARGET_COLUMN].astype(int))
        if classes != RISK_CLASSES:
            raise ValueError(
                f"{split_name} split must contain risk classes "
                f"{sorted(RISK_CLASSES)}; found {sorted(classes)}."
            )

    return train_indices, test_indices
