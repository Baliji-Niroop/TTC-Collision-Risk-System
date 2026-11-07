"""
generate_plots.py - Reproducible Result Plot Generator

Loads real validation data from data/synthetic_ttc_validation.csv and generates
clean, publication-ready figures saved directly to results/.

Generated plots:
1. results/ttc_vs_time.png: Dynamic TTC trajectory with SAFE/WARNING/CRITICAL threshold bands.
2. results/risk_distribution.png: Breakdown of driving time spent in each risk classification.
3. results/distance_speed_profile.png: Kinematic profile of vehicle distance and host speed.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Path setup
ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT_DIR / "data" / "synthetic_ttc_validation.csv"
RESULTS_DIR = ROOT_DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def plot_ttc_trajectory(df: pd.DataFrame) -> Path:
    """Generate TTC trajectory over time with standard risk threshold bands."""
    fig, ax = plt.subplots(figsize=(10, 5), dpi=300)

    # Use first 200 samples (20 seconds) for clear visibility
    sub_df = df.iloc[:200].copy()
    time_s = sub_df["timestamp_ms"] / 1000.0

    # Plot TTC curves
    ax.plot(
        time_s,
        sub_df["ttc_basic"].clip(upper=10.0),
        label="TTC Basic (Constant Velocity)",
        color="#1f77b4",
        linewidth=2.2,
    )
    ax.plot(
        time_s,
        sub_df["ttc_ext"].clip(upper=10.0),
        label="TTC Extended (Decel = 5.0 m/s²)",
        color="#2ca02c",
        linestyle="--",
        linewidth=2.0,
    )

    # Threshold horizontal lines
    ax.axhline(3.0, color="#f39c12", linestyle=":", linewidth=1.5, label="Warning Threshold (3.0s)")
    ax.axhline(1.5, color="#e74c3c", linestyle=":", linewidth=1.5, label="Critical Threshold (1.5s)")

    # Color zones
    ax.axhspan(3.0, 10.0, color="#2ecc71", alpha=0.10, label="Safe Zone (>3.0s)")
    ax.axhspan(1.5, 3.0, color="#f1c40f", alpha=0.15, label="Warning Zone (1.5s - 3.0s)")
    ax.axhspan(0.0, 1.5, color="#e74c3c", alpha=0.15, label="Critical Zone (<=1.5s)")

    ax.set_title("Time-To-Collision (TTC) Dynamic Response over Scenario Timeline", fontsize=12, fontweight="bold")
    ax.set_xlabel("Scenario Time (s)", fontsize=11)
    ax.set_ylabel("Time-To-Collision (s)", fontsize=11)
    ax.set_ylim(-0.2, 10.2)
    ax.set_xlim(time_s.min(), time_s.max())
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend(loc="upper right", framealpha=0.9, fontsize=9)

    out_path = RESULTS_DIR / "ttc_vs_time.png"
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close(fig)
    return out_path


def plot_risk_distribution(df: pd.DataFrame) -> Path:
    """Generate bar chart showing distribution of risk classes across dataset."""
    fig, ax = plt.subplots(figsize=(7, 4.5), dpi=300)

    risk_map = {0: "SAFE", 1: "WARNING", 2: "CRITICAL"}
    mapped_series = df["risk_class"].map(risk_map)
    counts = mapped_series.value_counts().reindex(["SAFE", "WARNING", "CRITICAL"], fill_value=0)
    percentages = (counts / len(df)) * 100.0

    colors = ["#2ecc71", "#f39c12", "#e74c3c"]
    bars = ax.bar(counts.index, counts.values, color=colors, edgecolor="#2c3e50", linewidth=1.2, width=0.5)

    for bar, pct, cnt in zip(bars, percentages, counts):
        height = bar.get_height()
        ax.annotate(
            f"{cnt} samples\n({pct:.1f}%)",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
        )

    ax.set_title(f"Risk Class Distribution Across Synthetic Benchmark (N = {len(df)})", fontsize=12, fontweight="bold")
    ax.set_ylabel("Number of Samples", fontsize=11)
    ax.set_ylim(0, max(counts.values) * 1.20)
    ax.grid(axis="y", linestyle="--", alpha=0.6)

    out_path = RESULTS_DIR / "risk_distribution.png"
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close(fig)
    return out_path


def main() -> None:
    if not DATA_FILE.exists():
        print(f"Error: Data file {DATA_FILE} not found.")
        sys.exit(1)

    df = pd.read_csv(DATA_FILE)
    print(f"Loaded dataset with {len(df)} rows from {DATA_FILE.name}")

    p1 = plot_ttc_trajectory(df)
    print(f"Saved: {p1}")

    p2 = plot_risk_distribution(df)
    print(f"Saved: {p2}")

    # Copy existing validation confusion matrix to results for unified reporting
    conf_src = ROOT_DIR / "validation" / "outputs" / "confusion_matrix.png"
    if conf_src.exists():
        import shutil
        conf_dst = RESULTS_DIR / "confusion_matrix.png"
        shutil.copyfile(conf_src, conf_dst)
        print(f"Copied confusion matrix to: {conf_dst}")


if __name__ == "__main__":
    main()
