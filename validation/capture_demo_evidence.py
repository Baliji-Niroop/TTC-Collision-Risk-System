"""
Capture pre-hardware demo evidence from a Wokwi bridge session.

Outputs under validation/outputs/demo_evidence/<session_id>/:
- canonical_session.csv
- risk_distribution.json
- confidence_trend.csv
- ttc_trend.csv
- alert_timeline.csv
- session_summary.json
- confidence_ttc_trends.png
- risk_distribution.png
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Iterable, List

import matplotlib.pyplot as plt

try:
    import websocket
except ImportError:  # pragma: no cover
    websocket = None

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
OUTPUT_ROOT = ROOT_DIR / "validation" / "outputs" / "demo_evidence"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from alerts import AlertManager  # noqa: E402
from validators import validate_csv_line  # noqa: E402

CANONICAL_HEADERS = [
    "timestamp_ms",
    "distance_cm",
    "speed_kmh",
    "ttc_basic",
    "ttc_ext",
    "risk_class",
    "confidence",
]

RISK_LABELS = {0: "SAFE", 1: "WARNING", 2: "CRITICAL"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capture Wokwi bridge evidence assets")
    parser.add_argument("--source", choices=["stdin", "websocket", "file"], default="stdin")
    parser.add_argument("--ws-url", default=None, help="Wokwi serial websocket URL")
    parser.add_argument("--input-file", default=None, help="Optional file containing canonical packets")
    parser.add_argument("--duration-sec", type=int, default=25, help="Capture duration in seconds")
    parser.add_argument("--min-rows", type=int, default=30, help="Minimum accepted canonical rows")
    parser.add_argument("--session-name", default=None, help="Optional fixed session folder name")
    return parser.parse_args()


def _extract_message_lines(message: str) -> List[str]:
    text = message.lstrip("\ufeff").strip()
    if not text:
        return []

    # Some websocket bridges send JSON envelopes. If JSON parse fails, treat as plain text.
    if text.startswith("{") and text.endswith("}"):
        try:
            payload = json.loads(text)
            data = payload.get("data") or payload.get("line") or payload.get("payload") or ""
            if isinstance(data, str):
                return [line.strip() for line in data.splitlines() if line.strip()]
        except json.JSONDecodeError:
            pass

    return [line.strip() for line in text.splitlines() if line.strip()]


def stdin_lines() -> Iterable[str]:
    for raw in sys.stdin:
        for line in _extract_message_lines(raw):
            yield line


def file_lines(path: Path) -> Iterable[str]:
    with path.open("r", encoding="utf-8") as handle:
        for raw in handle:
            for line in _extract_message_lines(raw):
                yield line


def websocket_lines(ws_url: str) -> Iterable[str]:
    if websocket is None:
        raise RuntimeError("websocket-client is required for websocket capture mode")

    retry_delay = 1.0
    while True:
        try:
            ws = websocket.create_connection(ws_url, timeout=10)
            retry_delay = 1.0
            while True:
                message = ws.recv()
                if message is None:
                    break
                if isinstance(message, bytes):
                    message = message.decode("utf-8", errors="ignore")
                for line in _extract_message_lines(str(message)):
                    yield line
        except KeyboardInterrupt:
            raise
        except Exception:
            time.sleep(retry_delay)
            retry_delay = min(10.0, retry_delay * 2.0)


def compute_linear_slope(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    n = len(values)
    x_values = list(range(n))
    x_mean = statistics.mean(x_values)
    y_mean = statistics.mean(values)
    numerator = sum((x_values[i] - x_mean) * (values[i] - y_mean) for i in range(n))
    denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _normalize_to_canonical_line(line: str) -> str | None:
    tokens = [token.strip() for token in line.split(",")]
    if len(tokens) < len(CANONICAL_HEADERS):
        return None

    canonical_tokens = tokens[: len(CANONICAL_HEADERS)]
    if any(any(ch.isalpha() for ch in token) for token in canonical_tokens):
        return None

    return ",".join(canonical_tokens)


def save_csv(path: Path, headers: List[str], rows: List[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in headers})


def save_trend_plot(path: Path, confidence_rows: List[dict], ttc_rows: List[dict]) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=True)

    axes[0].plot([r["sample_index"] for r in confidence_rows], [r["confidence"] for r in confidence_rows], color="#1f77b4")
    axes[0].set_title("Confidence Trend")
    axes[0].set_ylabel("confidence")
    axes[0].grid(alpha=0.3)

    axes[1].plot([r["sample_index"] for r in ttc_rows], [r["ttc_basic"] for r in ttc_rows], color="#d62728")
    axes[1].set_title("TTC Basic Trend")
    axes[1].set_xlabel("sample_index")
    axes[1].set_ylabel("ttc_basic (s)")
    axes[1].grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def save_distribution_plot(path: Path, distribution: dict) -> None:
    labels = ["SAFE", "WARNING", "CRITICAL"]
    values = [distribution.get(label, 0.0) for label in labels]
    colors = ["#2ca02c", "#ffbf00", "#d62728"]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(labels, values, color=colors)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Percentage")
    ax.set_title("Risk Distribution")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main() -> int:
    args = parse_args()

    session_id = args.session_name or datetime.now().strftime("demo_%Y%m%d_%H%M%S")
    out_dir = OUTPUT_ROOT / session_id
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.source == "websocket":
        if not args.ws_url:
            raise SystemExit("--ws-url is required in websocket mode")
        line_iter = websocket_lines(args.ws_url)
    elif args.source == "file":
        if not args.input_file:
            raise SystemExit("--input-file is required in file mode")
        line_iter = file_lines(Path(args.input_file))
    else:
        line_iter = stdin_lines()

    alert_manager = AlertManager()
    captured_rows = []
    confidence_rows = []
    ttc_rows = []
    alert_rows = []

    def on_alert(alert_data: dict) -> None:
        alert_rows.append(
            {
                "alert_time": alert_data.get("timestamp"),
                "risk_class": alert_data.get("risk_class"),
                "risk_label": alert_data.get("risk_label"),
                "ttc": alert_data.get("ttc"),
                "distance": alert_data.get("distance"),
                "speed": alert_data.get("speed"),
                "message": alert_data.get("message"),
            }
        )

    alert_manager.register_callback(on_alert)

    start = time.time()
    for line in line_iter:
        if time.time() - start > args.duration_sec:
            break

        canonical_line = _normalize_to_canonical_line(line)
        if canonical_line is None:
            print(f"REJECTED: {line}")
            continue

        row = validate_csv_line(canonical_line)
        if row is None:
            print(f"REJECTED: {line}")
            continue

        sample_index = len(captured_rows)
        row_out = {key: row[key] for key in CANONICAL_HEADERS}
        captured_rows.append(row_out)

        confidence_rows.append(
            {
                "sample_index": sample_index,
                "timestamp_ms": row["timestamp_ms"],
                "confidence": round(float(row["confidence"]), 6),
            }
        )
        ttc_rows.append(
            {
                "sample_index": sample_index,
                "timestamp_ms": row["timestamp_ms"],
                "ttc_basic": round(float(row["ttc_basic"]), 6),
                "ttc_ext": round(float(row["ttc_ext"]), 6),
            }
        )

        alert_manager.trigger_alert(int(row["risk_class"]), row)

    if len(captured_rows) < args.min_rows:
        print(
            f"WARNING: Only {len(captured_rows)} valid rows captured. "
            f"Increase --duration-sec or lower --min-rows."
        )

    risk_counts = {0: 0, 1: 0, 2: 0}
    for row in captured_rows:
        risk_counts[int(row["risk_class"])] += 1

    total = max(len(captured_rows), 1)
    risk_distribution = {
        RISK_LABELS[k]: round((v / total) * 100.0, 1)
        for k, v in risk_counts.items()
    }

    confidence_values = [float(r["confidence"]) for r in captured_rows]
    ttc_values = [float(r["ttc_basic"]) for r in captured_rows if math.isfinite(float(r["ttc_basic"]))]

    confidence_summary = {
        "min": round(min(confidence_values), 4) if confidence_values else 0.0,
        "max": round(max(confidence_values), 4) if confidence_values else 0.0,
        "mean": round(statistics.mean(confidence_values), 4) if confidence_values else 0.0,
        "slope_per_sample": round(compute_linear_slope(confidence_values), 6) if confidence_values else 0.0,
    }

    ttc_summary = {
        "min": round(min(ttc_values), 4) if ttc_values else 0.0,
        "max": round(max(ttc_values), 4) if ttc_values else 0.0,
        "mean": round(statistics.mean(ttc_values), 4) if ttc_values else 0.0,
        "slope_per_sample": round(compute_linear_slope(ttc_values), 6) if ttc_values else 0.0,
    }

    save_csv(out_dir / "canonical_session.csv", CANONICAL_HEADERS, captured_rows)
    save_csv(out_dir / "confidence_trend.csv", ["sample_index", "timestamp_ms", "confidence"], confidence_rows)
    save_csv(out_dir / "ttc_trend.csv", ["sample_index", "timestamp_ms", "ttc_basic", "ttc_ext"], ttc_rows)
    save_csv(
        out_dir / "alert_timeline.csv",
        ["alert_time", "risk_class", "risk_label", "ttc", "distance", "speed", "message"],
        alert_rows,
    )

    (out_dir / "risk_distribution.json").write_text(json.dumps(risk_distribution, indent=2), encoding="utf-8")

    session_summary = {
        "session_id": session_id,
        "capture_utc": datetime.utcnow().isoformat() + "Z",
        "source": args.source,
        "duration_sec": args.duration_sec,
        "rows_captured": len(captured_rows),
        "rows_recommended_min": args.min_rows,
        "risk_distribution": risk_distribution,
        "confidence_summary": confidence_summary,
        "ttc_summary": ttc_summary,
        "alerts_count": len(alert_rows),
        "output_dir": str(out_dir),
    }
    (out_dir / "session_summary.json").write_text(json.dumps(session_summary, indent=2), encoding="utf-8")

    if confidence_rows and ttc_rows:
        save_trend_plot(out_dir / "confidence_ttc_trends.png", confidence_rows, ttc_rows)
    save_distribution_plot(out_dir / "risk_distribution.png", risk_distribution)

    print(json.dumps(session_summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())