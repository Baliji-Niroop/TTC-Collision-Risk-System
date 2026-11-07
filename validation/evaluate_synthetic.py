"""Evaluate a trained model on scenarios kept out of model training."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.metrics import classification_report, confusion_matrix  # noqa: E402

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config import DATASET_DIR, MODEL_PATH, RISK_LABELS, RISK_THRESHOLDS, VALIDATION_DIR  # noqa: E402
from ml.inference import load_model  # noqa: E402
from ml.training.split import (  # noqa: E402
    FEATURE_COLUMNS,
    TARGET_COLUMN,
    scenario_train_test_indices,
)

DATASET_FILE = DATASET_DIR / "synthetic_ttc_validation.csv"
OUTPUT_DIR = VALIDATION_DIR / "outputs"
RESULTS_DIR = ROOT_DIR / "results"


def false_alarm_rate(
    y_true: np.ndarray, y_pred: np.ndarray, positive_class: int = 2
) -> float:
    negative_mask = y_true != positive_class
    if not np.any(negative_mask):
        return 0.0
    false_positives = np.sum((y_pred == positive_class) & negative_mask)
    total_negatives = np.sum(negative_mask)
    return float(false_positives / total_negatives)


def critical_recall(report_dict: dict) -> float:
    return float(report_dict.get("CRITICAL", {}).get("recall", 0.0))


def save_confusion_matrix(
    y_true: np.ndarray, y_pred: np.ndarray, output_path: Path, title: str
) -> None:
    labels = [0, 1, 2]
    matrix = confusion_matrix(y_true, y_pred, labels=labels)
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(matrix, cmap="Blues")
    ax.set_xticks(labels, [RISK_LABELS[label] for label in labels])
    ax.set_yticks(labels, [RISK_LABELS[label] for label in labels])
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title(title)

    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            ax.text(j, i, int(matrix[i, j]), ha="center", va="center", color="black")

    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def save_scenario_plot(df: pd.DataFrame, output_path: Path) -> None:
    summary = (
        df.groupby("scenario")
        .agg(
            mean_ttc=("ttc_basic", "mean"),
            mean_confidence=("predicted_confidence", "mean"),
            accuracy=("correct", "mean"),
        )
        .reset_index()
    )

    fig, ax = plt.subplots(figsize=(10, 4.5))
    x = np.arange(len(summary))
    width = 0.28
    ax.bar(x - width, summary["mean_ttc"], width, label="Mean TTC")
    ax.bar(x, summary["mean_confidence"], width, label="Mean confidence")
    ax.bar(x + width, summary["accuracy"], width, label="Accuracy")
    ax.set_xticks(x, summary["scenario"], rotation=20, ha="right")
    ax.set_title("Scenario Summary")
    ax.legend()
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def save_timeline_plot(df: pd.DataFrame, output_path: Path) -> None:
    fig, ax1 = plt.subplots(figsize=(11, 4.8))
    ax1.plot(df["timestamp_ms"], df["ttc_basic"], label="TTC basic", color="#1f77b4")
    ax1.plot(
        df["timestamp_ms"], df["ttc_ext"], label="TTC ext", color="#2ca02c", alpha=0.85
    )
    ax1.set_ylabel("TTC (s)")
    ax1.set_xlabel("Timestamp (ms)")
    ax1.legend(loc="upper right")
    ax1.grid(alpha=0.25)

    ax2 = ax1.twinx()
    ax2.plot(
        df["timestamp_ms"],
        df["predicted_confidence"],
        label="Predicted confidence",
        color="#d62728",
        alpha=0.6,
    )
    ax2.set_ylabel("Confidence")
    ax2.set_ylim(0, 1.05)

    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def main() -> None:
    if not DATASET_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATASET_FILE}. Run src/synthetic_validation_dataset.py first."
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    data = pd.read_csv(DATASET_FILE)
    data = data.dropna(subset=FEATURE_COLUMNS + [TARGET_COLUMN, "scenario"])
    train_indices, test_indices = scenario_train_test_indices(data)
    test_df = data.iloc[test_indices].copy()

    model = load_model()
    if model is None:
        raise RuntimeError(
            f"No trained model could be loaded from {MODEL_PATH}. "
            "Run `python ml/training/train_model.py` first; no model metrics "
            "were produced."
        )
    if not hasattr(model, "predict") or not hasattr(model, "predict_proba"):
        raise TypeError("The loaded model must implement predict and predict_proba.")

    y_true = test_df[TARGET_COLUMN].astype(int).to_numpy()
    features = test_df[FEATURE_COLUMNS]
    y_pred = model.predict(features).astype(int)
    test_df["predicted_risk_class"] = y_pred
    test_df["predicted_confidence"] = model.predict_proba(features).max(axis=1)
    test_df["correct"] = y_pred == y_true

    critical_threshold = test_df.get(
        "wet_critical_threshold_s", pd.Series(index=test_df.index, dtype=float)
    ).fillna(RISK_THRESHOLDS["critical"])
    warning_threshold = test_df.get(
        "wet_warning_threshold_s", pd.Series(index=test_df.index, dtype=float)
    ).fillna(RISK_THRESHOLDS["warning"])
    ttc = test_df["ttc_basic"].to_numpy()
    rule_predictions = np.where(
        ttc <= critical_threshold.to_numpy(),
        2,
        np.where(ttc <= warning_threshold.to_numpy(), 1, 0),
    )

    model_report = classification_report(
        y_true,
        y_pred,
        labels=[0, 1, 2],
        target_names=[RISK_LABELS[label] for label in [0, 1, 2]],
        output_dict=True,
        zero_division=0,
    )
    model_report_text = classification_report(
        y_true,
        y_pred,
        labels=[0, 1, 2],
        target_names=[RISK_LABELS[label] for label in [0, 1, 2]],
        zero_division=0,
    )
    rule_report = classification_report(
        y_true,
        rule_predictions,
        labels=[0, 1, 2],
        target_names=[RISK_LABELS[label] for label in [0, 1, 2]],
        output_dict=True,
        zero_division=0,
    )
    rule_report_text = classification_report(
        y_true,
        rule_predictions,
        labels=[0, 1, 2],
        target_names=[RISK_LABELS[label] for label in [0, 1, 2]],
        zero_division=0,
    )

    model_matrix = confusion_matrix(y_true, y_pred, labels=[0, 1, 2])
    model_metrics = {
        "accuracy": float(np.mean(y_true == y_pred)),
        "critical_recall": critical_recall(model_report),
        "false_alarm_rate": false_alarm_rate(y_true, y_pred),
        "confusion_matrix": model_matrix.tolist(),
        "classification_report": model_report,
    }
    rule_metrics = {
        "accuracy": float(np.mean(y_true == rule_predictions)),
        "critical_recall": critical_recall(rule_report),
        "false_alarm_rate": false_alarm_rate(y_true, rule_predictions),
        "confusion_matrix": confusion_matrix(
            y_true, rule_predictions, labels=[0, 1, 2]
        ).tolist(),
        "classification_report": rule_report,
    }

    test_df.to_csv(OUTPUT_DIR / "synthetic_predictions.csv", index=False)
    (OUTPUT_DIR / "classification_report.txt").write_text(
        "MODEL: Random Forest trained on scenario-disjoint TRAIN split\n"
        + model_report_text
        + "\nRULE BASELINE: TTC threshold rule on held-out TEST split\n"
        + rule_report_text,
        encoding="utf-8",
    )
    (OUTPUT_DIR / "summary.json").write_text(
        json.dumps(
            {
                "dataset": str(DATASET_FILE),
                "evaluation": "scenario-held-out",
                "model": "Random Forest",
                "train_rows": int(len(train_indices)),
                "test_rows": int(len(test_df)),
                "train_scenarios": sorted(
                    data.iloc[train_indices]["scenario"].unique().tolist()
                ),
                "test_scenarios": sorted(test_df["scenario"].unique().tolist()),
                "model_metrics": model_metrics,
                "rule_baseline_metrics": rule_metrics,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    save_confusion_matrix(
        y_true,
        y_pred,
        RESULTS_DIR / "confusion_matrix.png",
        "Random Forest: Held-Out Scenario Test",
    )
    save_scenario_plot(test_df, OUTPUT_DIR / "scenario_summary.png")
    save_timeline_plot(test_df, OUTPUT_DIR / "timeline_summary.png")

    test_scenarios = sorted(test_df["scenario"].unique().tolist())
    print(f"Trained model loaded from {MODEL_PATH}")
    print(f"Train scenarios: {sorted(data.iloc[train_indices]['scenario'].unique())}")
    print(f"Test scenarios: {test_scenarios}")
    print(
        "Random Forest held-out metrics: "
        f"accuracy={model_metrics['accuracy']:.3f}, "
        f"critical recall={model_metrics['critical_recall']:.3f}, "
        f"critical false-alarm rate={model_metrics['false_alarm_rate']:.3f}"
    )
    print(
        "TTC rule baseline held-out metrics: "
        f"accuracy={rule_metrics['accuracy']:.3f}, "
        f"critical recall={rule_metrics['critical_recall']:.3f}, "
        f"critical false-alarm rate={rule_metrics['false_alarm_rate']:.3f}"
    )
    print(f"Saved reports to {OUTPUT_DIR} and {RESULTS_DIR / 'confusion_matrix.png'}")
    print("\nRandom Forest classification report:")
    print(model_report_text)


if __name__ == "__main__":
    main()
