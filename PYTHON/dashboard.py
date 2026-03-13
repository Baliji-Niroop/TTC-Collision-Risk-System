from pathlib import Path

import streamlit as st
import time
import pandas as pd
import numpy as np
import joblib

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "ml_model.pkl"
DATA_PATH = BASE_DIR / "live_data.txt"

@st.cache_resource
def load_model(path: Path):
    return joblib.load(path)

model = load_model(MODEL_PATH)

st.set_page_config(page_title="TTC Dashboard", layout="wide")

st.title("🚗 Collision Risk Monitoring Dashboard")

ttc_placeholder = st.empty()
physics_placeholder = st.empty()
ml_placeholder = st.empty()
chart_placeholder = st.empty()
stats_placeholder = st.empty()
status_placeholder = st.empty()

# keep a rolling window to prevent unbounded memory growth
MAX_POINTS = 500

data = []

# session statistics
min_ttc = float("inf")
critical_count = 0

while True:

    try:
        with open(DATA_PATH, "r") as f:
            line = f.read().strip()
    except FileNotFoundError:
        status_placeholder.warning(f"Waiting for data file: {DATA_PATH}")
        time.sleep(0.2)
        continue
    except Exception:
        time.sleep(0.2)
        continue

    if not line:
        time.sleep(0.2)
        continue

    try:
        # Expecting: distance,ttc,risk
        distance_str, ttc_str, risk_str = [p.strip() for p in line.split(",")]
        distance = float(distance_str)
        ttc = float(ttc_str)
        risk = int(risk_str)
    except Exception:
        # ignore malformed data and wait for next update
        time.sleep(0.2)
        continue

    # clear any previous status messages
    status_placeholder.empty()

    # ---- ML prediction ----
    sample = np.array([[15, distance, 15, ttc, 0]])
    ml_risk = model.predict(sample)[0]

    # update statistics
    if ttc < min_ttc:
        min_ttc = ttc

    if risk == 2:
        critical_count += 1

    # store for chart (keep it bounded)
    data.append([distance, ttc])
    if len(data) > MAX_POINTS:
        data.pop(0)
    df = pd.DataFrame(data, columns=["Distance", "TTC"])


    # TTC display
    ttc_placeholder.metric("Time to Collision (s)", round(ttc, 2))

    # physics risk display
    if risk == 0:
        physics_placeholder.success("Physics Risk : SAFE")
    elif risk == 1:
        physics_placeholder.warning("Physics Risk : WARNING")
    else:
        physics_placeholder.error("Physics Risk : CRITICAL")

    # ML risk display
    if ml_risk == 0:
        ml_placeholder.success("ML Risk : SAFE")
    elif ml_risk == 1:
        ml_placeholder.warning("ML Risk : WARNING")
    else:
        ml_placeholder.error("ML Risk : CRITICAL")

    # chart
    chart_placeholder.line_chart(df)

    # statistics display
    stats_placeholder.write(
        f"### Minimum TTC observed : {round(min_ttc,2)} s"
    )
    stats_placeholder.write(
        f"### Critical events count : {critical_count}"
    )

    time.sleep(0.2)