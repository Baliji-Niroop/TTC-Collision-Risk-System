"""
replay_runner.py
Replay stored CSV sessions through validation, alerts, ML prediction, and analytics.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from alerts import check_and_alert  # noqa: E402
from analytics import SessionAnalytics, calculate_collision_probability, recommend_action  # noqa: E402
from config import DATA_PATH, LOG_DIR, RISK_LABELS  # noqa: E402
from ml.inference import load_model, predict_risk_with_confidence  # noqa: E402
from telemetry_schema import format_packet, parse_packet  # noqa: E402
from validators import validate_csv_line  # noqa: E402


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def _load_session(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except Exception:
        lines = [
            line.strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        rows = []
        for line in lines:
            parsed = parse_packet(line)
            if parsed:
                rows.append(parsed)
        return pd.DataFrame(rows)


def _save_replay_charts(df: pd.DataFrame, output_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(11, 4.8))
    ax.plot(df.index, df["ttc_basic"], label="TTC basic", color="#1f77b4")
    ax.plot(df.index, df["ttc_ext"], label="TTC ext", color="#2ca02c", alpha=0.85)
    ax.set_ylabel("TTC (s)")
    ax.set_xlabel("Replay step")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "replay_ttc.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(11, 4.8))
    ax.plot(
        df.index,
        df["predicted_confidence"],
        label="Predicted confidence",
        color="#d62728",
    )
    ax.plot(
        df.index,
        df["confidence"],
        label="Packet confidence",
        color="#ff7f0e",
        alpha=0.7,
    )
    ax.set_ylabel("Confidence")
    ax.set_xlabel("Replay step")
    ax.set_ylim(0, 1.05)
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "replay_confidence.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(11, 4.8))
    ax.step(
        df.index,
        df["predicted_risk_class"],
        where="post",
        label="Predicted risk",
        color="#b71c1c",
    )
    ax.step(
        df.index,
        df["risk_class"],
        where="post",
        label="Packet risk",
        color="#1f77b4",
        alpha=0.8,
    )
    ax.set_yticks([0, 1, 2], [RISK_LABELS[0], RISK_LABELS[1], RISK_LABELS[2]])
    ax.set_ylabel("Risk class")
    ax.set_xlabel("Replay step")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "replay_risk.png", dpi=180)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Replay a telemetry CSV session through the TTC pipeline."
    )
    parser.add_argument(
        "--input",
        type=str,
        default=str(DATA_PATH),
        help="Session CSV or packet log to replay",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(LOG_DIR / "replay_outputs"),
        help="Directory for replay artifacts",
    )
    parser.add_argument(
        "--interval-ms",
        type=float,
        default=0.0,
        help="Delay between packets during replay",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    session_df = _load_session(input_path)
    if session_df.empty:
        raise ValueError(f"No telemetry rows found in {input_path}")

    model = load_model()
    analytics = SessionAnalytics()
    replay_rows = []
    live_file = LOG_DIR / "live_data.txt"

    for _, row in session_df.iterrows():
        row_dict = row.to_dict()
        canonical_line = format_packet(row_dict)

        validated = validate_csv_line(canonical_line)
        if validated is None:
            continue

        parsed = parse_packet(canonical_line)
        if parsed is None:
            continue

        predicted_risk_class, predicted_confidence = predict_risk_with_confidence(
            parsed, model
        )
        packet_for_alerts = dict(parsed)
        packet_for_alerts["risk_class"] = predicted_risk_class
        packet_for_alerts["confidence"] = predicted_confidence

        alert_triggered = check_and_alert(predicted_risk_class, packet_for_alerts)
        action = recommend_action(
            predicted_risk_class, packet_for_alerts["ttc_basic"], predicted_confidence
        )
        collision_probability = calculate_collision_probability(
            packet_for_alerts["ttc_basic"], predicted_confidence
        )

        analytics.add_event(
            {
                "timestamp": packet_for_alerts["timestamp_ms"],
                "risk_class": predicted_risk_class,
                "ttc_basic": packet_for_alerts["ttc_basic"],
                "confidence": predicted_confidence,
            }
        )

        replay_rows.append(
            {
                **parsed,
                "predicted_risk_class": predicted_risk_class,
                "predicted_confidence": predicted_confidence,
                "alert_triggered": alert_triggered,
                "recommended_action": action,
                "collision_probability": collision_probability,
            }
        )

        _atomic_write(live_file, canonical_line)

        if args.interval_ms > 0:
            time.sleep(args.interval_ms / 1000.0)

    replay_df = pd.DataFrame(replay_rows)
    replay_df.to_csv(output_dir / "replay_results.csv", index=False)
    _save_replay_charts(replay_df, output_dir)

    summary = {
        "input": str(input_path),
        "model_loaded": model is not None,
        "rows_processed": int(len(replay_df)),
        "critical_events": (
            int((replay_df["predicted_risk_class"] == 2).sum()) if len(replay_df) else 0
        ),
        "warning_events": (
            int((replay_df["predicted_risk_class"] == 1).sum()) if len(replay_df) else 0
        ),
        "safe_events": (
            int((replay_df["predicted_risk_class"] == 0).sum()) if len(replay_df) else 0
        ),
        "mean_ttc": float(replay_df["ttc_basic"].mean()) if len(replay_df) else 0.0,
        "mean_confidence": (
            float(replay_df["predicted_confidence"].mean()) if len(replay_df) else 0.0
        ),
        "risk_distribution": analytics.get_risk_distribution(),
        "ttc_statistics": analytics.get_ttc_statistics(),
    }
    (output_dir / "replay_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    print(f"Replayed {len(replay_df)} rows from {input_path}")
    print(f"Replay artifacts written to {output_dir}")


if __name__ == "__main__":
    main()
