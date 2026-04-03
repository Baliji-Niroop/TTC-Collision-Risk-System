"""
evaluate_synthetic.py
Run the synthetic TTC dataset through the ML/physics pipeline and save reports.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config import DATASET_DIR, VALIDATION_DIR, RISK_LABELS
from ml.inference import load_model, predict_risk_with_confidence


DATASET_FILE = DATASET_DIR / "synthetic_ttc_validation.csv"
OUTPUT_DIR = VALIDATION_DIR / "outputs"


def false_alarm_rate(y_true: np.ndarray, y_pred: np.ndarray, positive_class: int = 2) -> float:
    negative_mask = y_true != positive_class
    if not np.any(negative_mask):
        return 0.0
    false_positives = np.sum((y_pred == positive_class) & negative_mask)
    total_negatives = np.sum(negative_mask)
    return float(false_positives / total_negatives)


def critical_recall(report_dict: dict) -> float:
    return float(report_dict.get("CRITICAL", {}).get("recall", 0.0))


def save_confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray, output_path: Path) -> None:
    labels = [0, 1, 2]
    matrix = confusion_matrix(y_true, y_pred, labels=labels)
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(matrix, cmap="Blues")
    ax.set_xticks(labels, [RISK_LABELS[label] for label in labels])
    ax.set_yticks(labels, [RISK_LABELS[label] for label in labels])
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title("Synthetic TTC Confusion Matrix")

    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            ax.text(j, i, int(matrix[i, j]), ha="center", va="center", color="black")

    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def save_scenario_plot(df: pd.DataFrame, output_path: Path) -> None:
    summary = df.groupby("scenario").agg(
        mean_ttc=("ttc_basic", "mean"),
        mean_confidence=("predicted_confidence", "mean"),
        accuracy=("correct", "mean"),
    ).reset_index()

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
    ax1.plot(df["timestamp_ms"], df["ttc_ext"], label="TTC ext", color="#2ca02c", alpha=0.85)
    ax1.set_ylabel("TTC (s)")
    ax1.set_xlabel("Timestamp (ms)")
    ax1.legend(loc="upper right")
    ax1.grid(alpha=0.25)

    ax2 = ax1.twinx()
    ax2.plot(df["timestamp_ms"], df["predicted_confidence"], label="Predicted confidence", color="#d62728", alpha=0.6)
    ax2.set_ylabel("Confidence")
    ax2.set_ylim(0, 1.05)

    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def main() -> None:
    if not DATASET_FILE.exists():
        raise FileNotFoundError(f"Dataset not found: {DATASET_FILE}. Run src/synthetic_validation_dataset.py first.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(DATASET_FILE)
    model = load_model()

    if "ground_truth_risk_class" not in df.columns:
        df["ground_truth_risk_class"] = df["risk_class"]

    predictions = df.apply(lambda row: predict_risk_with_confidence(row.to_dict(), model), axis=1)
    df["predicted_risk_class"] = predictions.apply(lambda value: int(value[0]))
    df["predicted_confidence"] = predictions.apply(lambda value: float(value[1]))
    df["correct"] = df["predicted_risk_class"] == df["ground_truth_risk_class"]

    y_true = df["ground_truth_risk_class"].astype(int).to_numpy()
    y_pred = df["predicted_risk_class"].astype(int).to_numpy()

    report = classification_report(
        y_true,
        y_pred,
        labels=[0, 1, 2],
        target_names=[RISK_LABELS[label] for label in [0, 1, 2]],
        output_dict=True,
        zero_division=0,
    )
    report_text = classification_report(
        y_true,
        y_pred,
        labels=[0, 1, 2],
        target_names=[RISK_LABELS[label] for label in [0, 1, 2]],
        zero_division=0,
    )

    matrix = confusion_matrix(y_true, y_pred, labels=[0, 1, 2])
    critical_idx = 2
    critical_recall_value = critical_recall(report)
    far = false_alarm_rate(y_true, y_pred, positive_class=critical_idx)

    df.to_csv(OUTPUT_DIR / "synthetic_predictions.csv", index=False)
    (OUTPUT_DIR / "classification_report.txt").write_text(report_text, encoding="utf-8")
    (OUTPUT_DIR / "summary.json").write_text(
        json.dumps(
            {
                "dataset": str(DATASET_FILE),
                "model_loaded": model is not None,
                "rows": int(len(df)),
                "accuracy": float((df["correct"].mean() if len(df) else 0.0)),
                "critical_recall": critical_recall_value,
                "false_alarm_rate": far,
                "confusion_matrix": matrix.tolist(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    save_confusion_matrix(y_true, y_pred, OUTPUT_DIR / "confusion_matrix.png")
    save_scenario_plot(df, OUTPUT_DIR / "scenario_summary.png")
    save_timeline_plot(df, OUTPUT_DIR / "timeline_summary.png")

    print(f"Saved reports to {OUTPUT_DIR}")
    print(f"Critical recall: {critical_recall_value:.3f}")
    print(f"False alarm rate: {far:.3f}")
    print(report_text)


if __name__ == "__main__":
    main()
