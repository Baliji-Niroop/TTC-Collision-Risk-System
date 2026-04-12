"""
Compare a Wokwi capture against the current replay baseline.

Expected input is a strict canonical CSV with columns:
timestamp_ms,distance_cm,speed_kmh,ttc_basic,ttc_ext,risk_class,confidence
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_BASELINE = BASE_DIR / "LOGS" / "replay_outputs" / "replay_summary.json"
ARCHIVED_BASELINE = (
    BASE_DIR / "LOGS" / "archive" / "replay_outputs" / "replay_summary.json"
)

RISK_LABELS = {0: "SAFE", 1: "WARNING", 2: "CRITICAL"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare Wokwi telemetry against replay baselines"
    )
    parser.add_argument(
        "--input", required=True, help="Path to a canonical CSV captured from Wokwi"
    )
    parser.add_argument(
        "--baseline",
        default=str(DEFAULT_BASELINE),
        help="Replay summary JSON used as the baseline",
    )
    parser.add_argument(
        "--output", default=None, help="Optional path to write the comparison JSON"
    )
    return parser.parse_args()


def resolve_baseline_path(candidate: Path) -> Path:
    if candidate.exists():
        return candidate

    if candidate.resolve() == DEFAULT_BASELINE.resolve() and ARCHIVED_BASELINE.exists():
        return ARCHIVED_BASELINE

    return candidate


def load_rows(csv_path: Path) -> list[dict]:
    rows: list[dict] = []
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        for line_number, parts in enumerate(reader, start=1):
            if len(parts) < 7:
                continue

            # Accept richer datasets by consuming only canonical packet fields.
            parts = [part.strip() for part in parts[:7]]
            if any(any(ch.isalpha() for ch in token) for token in parts):
                continue

            try:
                row = {
                    "timestamp_ms": float(parts[0]),
                    "distance_cm": float(parts[1]),
                    "speed_kmh": float(parts[2]),
                    "ttc_basic": float(parts[3]),
                    "ttc_ext": float(parts[4]),
                    "risk_class": int(float(parts[5])),
                    "confidence": float(parts[6]),
                }
            except ValueError:
                continue

            if row["risk_class"] not in RISK_LABELS:
                continue
            if not math.isfinite(row["confidence"]):
                continue
            rows.append(row)
    return rows


def summarize(rows: list[dict]) -> dict:
    total = len(rows)
    counts = {0: 0, 1: 0, 2: 0}
    confidences = []
    for row in rows:
        counts[row["risk_class"]] += 1
        confidences.append(row["confidence"])

    if total:
        distribution = {
            RISK_LABELS[risk_class]: round((count / total) * 100.0, 1)
            for risk_class, count in counts.items()
        }
        mean_confidence = sum(confidences) / total
        start_slice = confidences[: max(1, total // 3)]
        end_slice = confidences[-max(1, total // 3) :]
        confidence_trend = {
            "start_mean": round(sum(start_slice) / len(start_slice), 4),
            "end_mean": round(sum(end_slice) / len(end_slice), 4),
            "delta": round(
                (sum(end_slice) / len(end_slice))
                - (sum(start_slice) / len(start_slice)),
                4,
            ),
        }
    else:
        distribution = {label: 0.0 for label in RISK_LABELS.values()}
        mean_confidence = 0.0
        confidence_trend = {"start_mean": 0.0, "end_mean": 0.0, "delta": 0.0}

    return {
        "rows": total,
        "critical_events": counts[2],
        "warning_events": counts[1],
        "safe_events": counts[0],
        "mean_confidence": round(mean_confidence, 6),
        "risk_distribution": distribution,
        "confidence_trend": confidence_trend,
    }


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    baseline_path = resolve_baseline_path(Path(args.baseline))

    rows = load_rows(input_path)
    summary = summarize(rows)

    baseline = {}
    if baseline_path.exists():
        with baseline_path.open("r", encoding="utf-8") as handle:
            baseline = json.load(handle)

    comparison = {
        "input": str(input_path),
        "baseline": str(baseline_path),
        "summary": summary,
        "baseline_reference": {
            "rows_processed": baseline.get("rows_processed"),
            "mean_confidence": baseline.get("mean_confidence"),
            "risk_distribution": baseline.get("risk_distribution"),
        },
    }

    if baseline.get("risk_distribution"):
        deltas = {}
        for label in ("SAFE", "WARNING", "CRITICAL"):
            deltas[label] = round(
                summary["risk_distribution"][label]
                - float(baseline["risk_distribution"].get(label, 0.0)),
                1,
            )
        comparison["distribution_delta_vs_baseline"] = deltas

    rendered = json.dumps(comparison, indent=2)
    print(rendered)

    output_path = Path(args.output) if args.output else None
    if output_path:
        output_path.write_text(rendered, encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
