"""
TTC Collision Risk Monitoring Dashboard
========================================
Adaptive Collision Risk Prediction System

This is the main dashboard application for real-time TTC (Time-to-Collision)
monitoring. It visualises live or simulated telemetry data alongside an ML-based
risk classifier to provide a continuous overview of forward-collision risk.

Data Sources (selectable from the sidebar):
  - Simulator    : Physics-based synthetic data generated in-process.
                   No hardware or external files needed.
  - Live Log     : Reads the most recent line from LOGS/live_data.txt,
                   which is written by serial_simulator.py or serial_reader.py.
  - ESP32 Serial : Reads directly from a USB serial port (requires pyserial).
                   Used when an ESP32 with an ultrasonic sensor is connected.

How it works:
  1. Each refresh cycle (~0.6 s) a new telemetry row is obtained from the
     selected data source.
  2. The row is passed through the ML model (Random Forest) to predict a
     risk class (0 = Safe, 1 = Warning, 2 = Critical).  If the model is
     unavailable, a physics-based fallback using TTC thresholds is used.
  3. Metrics, trend charts, event log, and session statistics are updated.

Usage:
    pip install streamlit pandas numpy joblib scikit-learn
    streamlit run dashboard.py
"""

# ---------------------------------------------------------------------------
# Standard library imports
# ---------------------------------------------------------------------------
import time
import math
import random
from pathlib import Path

# ---------------------------------------------------------------------------
# Third-party imports
# ---------------------------------------------------------------------------
import pandas as pd
import numpy as np
import streamlit as st

# ---------------------------------------------------------------------------
# Path Configuration
# ---------------------------------------------------------------------------
# BASE_DIR points to the PYTHON/ folder where this script lives.
# ROOT_DIR is the project root (one level up) — this is where MODELS/ and
# LOGS/ directories are located.
BASE_DIR   = Path(__file__).resolve().parent
ROOT_DIR   = BASE_DIR.parent
MODEL_PATH = ROOT_DIR / "MODELS" / "ml_model.pkl"
DATA_PATH  = ROOT_DIR / "LOGS"   / "live_data.txt"

# ---------------------------------------------------------------------------
# Dashboard Constants
# ---------------------------------------------------------------------------
MAX_POINTS  = 120       # Number of data points kept in the rolling chart buffer
REFRESH_SEC = 0.6       # Seconds between each dashboard refresh cycle

# Risk class labels and their corresponding banner colours.
# Class 0 = Safe, Class 1 = Warning, Class 2 = Critical.
RISK_LABELS = {0: "SAFE", 1: "WARNING", 2: "CRITICAL"}
RISK_COLORS = {
    0: ("SAFE",     "#1a7a2e"),   # Green
    1: ("WARNING",  "#b36b00"),   # Amber
    2: ("CRITICAL", "#b71c1c"),   # Red
}

# ---------------------------------------------------------------------------
# Streamlit Page Configuration (must be the first Streamlit call)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="TTC Collision Risk Dashboard",
    layout="wide",
    page_icon="🚗",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
# Injects styling for metric cards, risk-banner animations, chart containers,
# sidebar adjustments, and footer branding.  All visual refinements live here
# so the Python logic stays free of inline style strings.
st.markdown("""
<style>
/* ---------- Risk banner pulse animations ---------- */
@keyframes pulse-critical {
    0%, 100% { box-shadow: 0 0 0 0 rgba(183,28,28,0.4); }
    50%      { box-shadow: 0 0 20px 6px rgba(183,28,28,0.2); }
}
.risk-banner-critical { animation: pulse-critical 1.2s ease-in-out infinite; }

@keyframes pulse-warning {
    0%, 100% { box-shadow: 0 0 0 0 rgba(179,107,0,0.35); }
    50%      { box-shadow: 0 0 16px 5px rgba(179,107,0,0.18); }
}
.risk-banner-warning { animation: pulse-warning 1.5s ease-in-out infinite; }

/* ---------- Metric cards ---------- */
div[data-testid="stMetric"] {
    background: linear-gradient(135deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02));
    border: 1px solid rgba(128,128,128,0.14);
    border-radius: 10px;
    padding: 12px 16px;
    box-shadow: 0 1px 6px rgba(0,0,0,0.05);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
div[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 14px rgba(0,0,0,0.09);
}

/* ---------- Chart containers ---------- */
div[data-testid="stVegaLiteChart"] {
    border: 1px solid rgba(128,128,128,0.10);
    border-radius: 8px;
    padding: 6px;
}

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] > div { padding-top: 1.4rem; }

/* ---------- Footer ---------- */
.footer-brand {
    text-align: center;
    color: #999;
    font-size: 0.75rem;
    padding: 20px 0 8px 0;
    border-top: 1px solid rgba(128,128,128,0.12);
    margin-top: 28px;
    letter-spacing: 0.3px;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Optional Imports (pyserial for hardware, joblib for ML model)
# ---------------------------------------------------------------------------
# pyserial is only needed when reading from an actual ESP32 over USB.
# If it is not installed, the "ESP32 Serial" option is hidden from the sidebar.
try:
    import serial
    import serial.tools.list_ports
    _SERIAL_OK = True
except ImportError:
    _SERIAL_OK = False


# ---------------------------------------------------------------------------
# ML Model Loading
# ---------------------------------------------------------------------------
# The model is a scikit-learn Random Forest classifier trained on TTC features
# (speed, distance, closing velocity, ttc, road type).  It is loaded once and
# cached for the lifetime of the Streamlit process.  If the .pkl file is
# missing or cannot be loaded, the dashboard falls back to a simple
# physics-based threshold classifier instead.
@st.cache_resource(show_spinner=False)
def _load_model():
    """Load the pre-trained ML model from disk (cached across reruns)."""
    try:
        import joblib
        if MODEL_PATH.exists():
            return joblib.load(MODEL_PATH)
    except Exception:
        pass
    return None


model = _load_model()

# ---------------------------------------------------------------------------
# Session State Initialisation
# ---------------------------------------------------------------------------
# Streamlit reruns the entire script on every refresh.  Session state preserves
# values across reruns so that rolling buffers, counters, and simulator
# variables persist throughout a session.
_STATE_DEFAULTS = {
    "buffer":         [],       # Rolling list of dicts for trend charts
    "min_ttc":        99.0,     # Lowest TTC observed this session (seconds)
    "max_speed":      0.0,      # Highest speed observed this session (km/h)
    "critical_count": 0,        # Cumulative count of CRITICAL risk events
    "warning_count":  0,        # Cumulative count of WARNING risk events
    "safe_count":     0,        # Cumulative count of SAFE events
    "session_start":  time.time(),
    "log_rows":       [],       # Full event log kept for CSV export
    "sim_d":          8.0,      # Simulator state: current distance (m)
    "sim_v":          1.0,      # Simulator state: current velocity (m/s)
    "sim_t":          0,        # Simulator state: tick counter
}
for _k, _v in _STATE_DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ═══════════════════════════════════════════════════════════════════════════
#  DATA SOURCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def simulate_step() -> dict:
    """
    Generate one tick of simulated sensor data.

    The simulator models a vehicle approaching an obstacle using a
    sine-wave velocity profile so that the TTC naturally oscillates
    through all three risk zones (Safe → Warning → Critical → reset).

    Physics:
        distance -= velocity * dt
        TTC_basic = distance / closing_velocity       (constant-speed model)
        TTC_ext   = (-v + sqrt(v² + 2·a·d)) / a      (constant-deceleration model)

    Returns a dict with keys: distance_cm, speed_kmh, ttc_basic, ttc_ext,
    risk_phys, confidence.
    """
    dt = REFRESH_SEC
    d  = st.session_state.sim_d
    v  = st.session_state.sim_v

    # Advance the tick counter
    st.session_state.sim_t += 1
    t = st.session_state.sim_t

    # The target velocity follows a slow sine wave so the simulated TTC
    # sweeps through SAFE, WARNING, and CRITICAL zones over time.
    target_v = 3.5 * math.sin(t * 0.07) + random.gauss(0, 0.1)
    v += (target_v - v) * 0.2       # Smoothly blend towards target
    v  = max(-2.0, min(v, 8.0))     # Clamp to realistic range

    # Update distance based on velocity and time step
    d -= v * dt

    # If the vehicle is too close, reset to a new random distance (simulates
    # the obstacle reappearing further away after a near-collision).
    if d < 0.3:
        d = random.uniform(6.0, 10.0)
        v = random.uniform(0.5, 2.5)

    # If the vehicle drifts too far away, nudge it back inward
    if d > 15.0:
        v = max(v, 0.5)

    # Persist updated state for the next tick
    st.session_state.sim_d = d
    st.session_state.sim_v = v

    # --- TTC Calculations ---
    # Closing velocity is the component of velocity directed toward the obstacle.
    v_close = max(v, 0.0)

    # Basic TTC: assumes the closing velocity remains constant.
    # If the vehicle is barely moving, report a high TTC (no imminent risk).
    ttc_basic = (d / v_close) if v_close > 0.1 else 99.0
    ttc_basic = round(min(ttc_basic, 99.0), 2)

    # Extended TTC: assumes the vehicle decelerates at a_decel m/s².
    # Uses the kinematic equation:  d = v·t + ½·a·t²  →  solve for t.
    a_decel = 5.0
    disc    = v_close ** 2 + 2 * a_decel * d
    ttc_ext = (-v_close + math.sqrt(max(disc, 0.0))) / a_decel
    ttc_ext = round(min(ttc_ext, 99.0), 2)

    # Physics-based risk classification using TTC thresholds
    risk = 0 if ttc_basic > 3.0 else (1 if ttc_basic > 1.5 else 2)

    return {
        "distance_cm": round(d * 100, 1),
        "speed_kmh":   round(abs(v) * 3.6, 1),
        "ttc_basic":   ttc_basic,
        "ttc_ext":     ttc_ext,
        "risk_phys":   risk,
        "confidence":  round(random.uniform(0.76, 0.99), 2),
    }


def parse_csv_line(line: str):
    """
    Parse a single CSV line from the telemetry log or serial stream.

    Expected format (7 comma-separated fields):
        timestamp_ms, distance_cm, speed_kmh, ttc_basic, ttc_ext, risk_class, confidence

    Returns a dict with the parsed values, or None if the line is malformed.
    """
    try:
        parts = [p.strip() for p in line.split(",")]
        if len(parts) != 7:
            return None
        return {
            "distance_cm": float(parts[1]),
            "speed_kmh":   float(parts[2]),
            "ttc_basic":   float(parts[3]),
            "ttc_ext":     float(parts[4]),
            "risk_phys":   int(float(parts[5])),
            "confidence":  float(parts[6]),
        }
    except (ValueError, IndexError):
        return None


def read_log_file():
    """
    Read the most recent telemetry reading from the live data file.

    The simulator and serial reader both overwrite LOGS/live_data.txt with
    a single CSV line on each tick.  This function reads that file, finds
    the last non-empty line, and parses it.
    """
    try:
        lines = DATA_PATH.read_text(encoding="utf-8").splitlines()
        for line in reversed(lines):
            if line.strip():
                return parse_csv_line(line.strip())
    except FileNotFoundError:
        return None
    except Exception:
        return None
    return None


@st.cache_resource(show_spinner=False)
def _open_serial(port: str):
    """Open a serial port connection, cached for the Streamlit session."""
    try:
        return serial.Serial(port, 115200, timeout=1)
    except Exception:
        return None


def read_serial(port: str):
    """
    Read one CSV line from the ESP32 serial port and parse it.

    The ESP32 firmware is expected to output comma-separated telemetry at
    115200 baud in the same 7-field format used by parse_csv_line().
    """
    try:
        ser = _open_serial(port)
        if ser is None or not ser.is_open:
            return None
        raw = ser.readline().decode("utf-8", errors="ignore").strip()
        return parse_csv_line(raw)
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════════
#  ML PREDICTION
# ═══════════════════════════════════════════════════════════════════════════

def ml_predict(row: dict) -> int:
    """
    Predict the collision risk class using the ML model.

    The Random Forest model was trained on five features:
        speed, distance, closing_vel, ttc, road

    If the model is not available (file missing or load failed), the
    function falls back to the physics-based risk class already computed
    by the data source.
    """
    if model is None:
        return row["risk_phys"]
    try:
        d_m       = row["distance_cm"] / 100.0
        spd       = row["speed_kmh"]
        ttc       = row["ttc_basic"]
        close_vel = d_m / max(ttc, 0.1)     # Approximate closing velocity (m/s)

        feature_dict = {
            "speed": spd,
            "distance": d_m,
            "closing_vel": close_vel,
            "ttc": ttc,
            "road": 0
        }

        # Align to expected features if stored; else default
        if hasattr(model, "expected_features"):
            expected_cols = model.expected_features
        elif hasattr(model, "feature_names_in_"):
            expected_cols = list(model.feature_names_in_)
        else:
            expected_cols = ["speed", "distance", "closing_vel", "ttc", "road"]

        features = pd.DataFrame([{col: feature_dict.get(col, 0) for col in expected_cols}], columns=expected_cols)

        return int(model.predict(features)[0])
    except Exception:
        return row["risk_phys"]


# ═══════════════════════════════════════════════════════════════════════════
#  SIDEBAR — Configuration & Status
# ═══════════════════════════════════════════════════════════════════════════

st.sidebar.title("Configuration")

if not _SERIAL_OK:
    st.sidebar.warning("`pyserial` not installed. 'ESP32 Serial' mode disabled. Run `pip install pyserial`.")

# --- Data source selector ---
# Available modes depend on what is installed / present on disk.
_mode_opts = ["Simulator", "Live Log"]
if _SERIAL_OK:
    _mode_opts.append("ESP32 Serial")

mode = st.sidebar.radio("Data Source", _mode_opts)

# If ESP32 mode is selected, show a dropdown of available COM ports
serial_port = None
if mode == "ESP32 Serial" and _SERIAL_OK:
    _ports = [p.device for p in serial.tools.list_ports.comports()]
    if _ports:
        serial_port = st.sidebar.selectbox("COM Port", _ports)
    else:
        st.sidebar.error("No serial ports detected. Check USB cable.")

st.sidebar.markdown("---")

# --- System status ---
st.sidebar.markdown(
    f"**ML Model:** {'Loaded' if model else 'Not found — using physics fallback'}"
)
st.sidebar.markdown(
    f"**pyserial:** {'Available' if _SERIAL_OK else 'Not installed'}"
)
st.sidebar.markdown(f"**Refresh interval:** {REFRESH_SEC} s")

st.sidebar.markdown("---")

auto_refresh = st.sidebar.checkbox("Auto refresh", value=True)

# --- Adjustable TTC thresholds ---
# These sliders let the user tune what TTC values correspond to each risk
# level.  Useful for calibrating different driving scenarios (highway vs city).
st.sidebar.subheader("Fallback Thresholds (used only when ML not loaded)")
thresh_warn = st.sidebar.slider(
    "Warning TTC (s)", 1.0, 5.0, 3.0, 0.1,
    help="TTC values below this are classified as WARNING",
    disabled=(model is not None)
)
thresh_crit = st.sidebar.slider(
    "Critical TTC (s)", 0.5, 3.0, 1.5, 0.1,
    help="TTC values below this are classified as CRITICAL",
    disabled=(model is not None)
)
if thresh_crit >= thresh_warn:
    st.sidebar.error("Critical threshold must be less than Warning threshold.")
    thresh_crit = thresh_warn - 0.5

st.sidebar.markdown("---")

if st.sidebar.button("Reset Session"):
    for _k in list(_STATE_DEFAULTS.keys()):
        if _k in st.session_state:
            del st.session_state[_k]
    st.rerun()


# ═══════════════════════════════════════════════════════════════════════════
#  FETCH DATA — obtain one telemetry row from the selected source
# ═══════════════════════════════════════════════════════════════════════════

if mode == "Simulator":
    row = simulate_step()

elif mode == "Live Log":
    row = read_log_file()
    if row is None:
        st.warning("Waiting for data in LOGS/live_data.txt …")
        time.sleep(1)
        st.rerun()

else:   # ESP32 Serial
    if serial_port is None:
        st.error("No serial port selected.")
        st.stop()
    row = read_serial(serial_port)
    if row is None:
        st.warning("Waiting for ESP32 serial data …")
        time.sleep(1)
        st.rerun()


# ═══════════════════════════════════════════════════════════════════════════
#  PROCESS — classify risk and update session statistics
# ═══════════════════════════════════════════════════════════════════════════

risk  = ml_predict(row)
ttc_b = row["ttc_basic"]

# When the ML model is not available, apply the user-configured thresholds
# for the physics-based fallback classifier.
if model is None:
    risk = 0 if ttc_b > thresh_warn else (1 if ttc_b > thresh_crit else 2)

# Update running session statistics
if ttc_b < st.session_state.min_ttc:
    st.session_state.min_ttc = ttc_b
if row["speed_kmh"] > st.session_state.max_speed:
    st.session_state.max_speed = row["speed_kmh"]

if risk == 2:
    st.session_state.critical_count += 1
elif risk == 1:
    st.session_state.warning_count += 1
else:
    st.session_state.safe_count += 1

# Append current values to the rolling chart buffer (oldest entries are
# dropped once the buffer exceeds MAX_POINTS).
st.session_state.buffer.append({
    "TTC Basic (s)": ttc_b,
    "TTC Ext (s)":   row["ttc_ext"],
    "Distance (m)":  round(row["distance_cm"] / 100, 2),
    "Speed (km/h)":  row["speed_kmh"],
})
if len(st.session_state.buffer) > MAX_POINTS:
    st.session_state.buffer.pop(0)

df = pd.DataFrame(st.session_state.buffer)

# Append to the full event log (used for the data table and CSV export)
st.session_state.log_rows.append({
    "time":          time.strftime("%H:%M:%S"),
    "ttc_basic_s":   ttc_b,
    "ttc_ext_s":     row["ttc_ext"],
    "distance_m":    round(row["distance_cm"] / 100, 3),
    "speed_kmh":     row["speed_kmh"],
    "risk":          RISK_LABELS[risk],
    "confidence_%":  round(row["confidence"] * 100, 1),
})


# ═══════════════════════════════════════════════════════════════════════════
#  RENDER — Dashboard Layout
# ═══════════════════════════════════════════════════════════════════════════

# --- Header ---
st.title("TTC Collision Risk Dashboard")
st.caption(
    f"Adaptive Collision Risk Prediction System  ·  "
    f"Source: {mode}  ·  {time.strftime('%H:%M:%S')}"
)

# --- Risk Status Banner ---
# The banner uses a soft pulse animation when the risk is WARNING or CRITICAL
# to draw the user's attention without being distracting.
label, color = RISK_COLORS[risk]
anim_class = {2: "risk-banner-critical", 1: "risk-banner-warning"}.get(risk, "")

st.markdown(
    f'<div class="{anim_class}" style="background:{color};color:white;'
    f'text-align:center;padding:16px;border-radius:8px;'
    f'font-size:1.8rem;font-weight:700;letter-spacing:1px;margin-bottom:6px;">'
    f'{label}</div>',
    unsafe_allow_html=True,
)
st.markdown("")

# --- Primary Telemetry Metrics ---
c1, c2, c3, c4 = st.columns(4)
prev_ttc = df["TTC Basic (s)"].iloc[-2] if len(df) >= 2 else None
c1.metric("TTC Basic",    f"{ttc_b:.2f} s",
          delta=f"{ttc_b - prev_ttc:.2f} s" if prev_ttc is not None else None)
c2.metric("TTC Extended", f"{row['ttc_ext']:.2f} s")
c3.metric("Distance",     f"{row['distance_cm'] / 100:.2f} m")
c4.metric("Speed",        f"{row['speed_kmh']:.1f} km/h")

st.markdown("---")

# --- Session Statistics ---
c5, c6, c7, c8 = st.columns(4)
c5.metric("Confidence",        f"{row['confidence'] * 100:.0f}%")
c6.metric("Min TTC (session)", f"{st.session_state.min_ttc:.2f} s")
c7.metric("Critical Events",   st.session_state.critical_count)
c8.metric("Warning Events",    st.session_state.warning_count)

st.markdown("---")

# --- Trend Charts (side by side) ---
col_l, col_r = st.columns(2)
with col_l:
    st.subheader("TTC Trend")
    if len(df) >= 2:
        st.line_chart(df[["TTC Basic (s)", "TTC Ext (s)"]], height=280)
    else:
        st.info("Collecting data …")

with col_r:
    st.subheader("Distance & Speed Trend")
    if len(df) >= 2:
        st.line_chart(df[["Distance (m)", "Speed (km/h)"]], height=280)
    else:
        st.info("Collecting data …")

st.markdown("---")

# --- Risk Distribution ---
# Shows how much time the system spent in each risk zone during this session.
st.subheader("Risk Distribution")
col_dist_l, col_dist_r = st.columns([2, 1])

total_events = (
    st.session_state.safe_count
    + st.session_state.warning_count
    + st.session_state.critical_count
)

with col_dist_l:
    if total_events > 0:
        dist_df = pd.DataFrame({
            "Risk Level": ["SAFE", "WARNING", "CRITICAL"],
            "Count":      [
                st.session_state.safe_count,
                st.session_state.warning_count,
                st.session_state.critical_count,
            ],
        })
        st.bar_chart(dist_df.set_index("Risk Level"), height=200)

with col_dist_r:
    if total_events > 0:
        safe_pct = round(st.session_state.safe_count / total_events * 100, 1)
        warn_pct = round(st.session_state.warning_count / total_events * 100, 1)
        crit_pct = round(st.session_state.critical_count / total_events * 100, 1)
        st.markdown(
            f"| Status | Count | % |\n"
            f"|--------|------:|---:|\n"
            f"| SAFE | {st.session_state.safe_count} | {safe_pct}% |\n"
            f"| WARNING | {st.session_state.warning_count} | {warn_pct}% |\n"
            f"| CRITICAL | {st.session_state.critical_count} | {crit_pct}% |"
        )

st.markdown("---")

# --- Risk Zone Reference ---
# Quick-reference cards showing the TTC boundaries for each risk level.
# These update dynamically if the user adjusts the threshold sliders.
st.subheader("Risk Zone Reference")
z1, z2, z3 = st.columns(3)
z1.success(f"SAFE — TTC > {thresh_warn:.1f} s")
z2.warning(f"WARNING — {thresh_crit:.1f} s to {thresh_warn:.1f} s")
z3.error(f"CRITICAL — TTC < {thresh_crit:.1f} s")

st.markdown("---")

# --- Event Log ---
# Displays the most recent 30 telemetry readings in a table.  CRITICAL and
# WARNING rows are tinted red/amber so dangerous events are easy to spot.
st.subheader("Event Log")
if st.session_state.log_rows:
    log_df = pd.DataFrame(st.session_state.log_rows).tail(30)

    def _highlight_risk(row):
        """Apply background tint to WARNING and CRITICAL rows."""
        if row["risk"] == "CRITICAL":
            return ["background-color: rgba(183,28,28,0.12)"] * len(row)
        elif row["risk"] == "WARNING":
            return ["background-color: rgba(179,107,0,0.10)"] * len(row)
        return [""] * len(row)

    styled_log = log_df.style.apply(_highlight_risk, axis=1)
    st.dataframe(styled_log, use_container_width=True, height=240)

    # CSV export of the full session log (not just the last 30 rows)
    csv_bytes = (
        pd.DataFrame(st.session_state.log_rows)
        .to_csv(index=False)
        .encode("utf-8")
    )
    st.download_button(
        "Download Session CSV",
        data=csv_bytes,
        file_name=f"ttc_session_{int(time.time())}.csv",
        mime="text/csv",
    )
else:
    st.info("No events recorded yet.")

st.markdown("---")

# --- Session Summary ---
elapsed  = int(time.time() - st.session_state.session_start)
h, rem   = divmod(elapsed, 3600)
m_t, s_t = divmod(rem, 60)
total    = max(len(st.session_state.log_rows), 1)
safe_pct = round(
    sum(1 for r in st.session_state.log_rows if r["risk"] == "SAFE") / total * 100
)

st.subheader("Session Summary")
s1, s2, s3, s4 = st.columns(4)
s1.metric("Duration",       f"{h:02d}:{m_t:02d}:{s_t:02d}")
s2.metric("Total Readings", total)
s3.metric("Time Safe",      f"{safe_pct}%")
s4.metric("Mean TTC",
          f"{df['TTC Basic (s)'].mean():.2f} s" if len(df) > 0 else "—")

s5, s6, s7, s8 = st.columns(4)
s5.metric("Max Speed",      f"{st.session_state.max_speed:.1f} km/h")
s6.metric("Avg Distance",
          f"{df['Distance (m)'].mean():.2f} m" if len(df) > 0 else "—")
s7.metric("Avg Speed",
          f"{df['Speed (km/h)'].mean():.1f} km/h" if len(df) > 0 else "—")
s8.metric("Avg Confidence",
          f"{sum(r['confidence_%'] for r in st.session_state.log_rows) / total:.0f}%"
          if st.session_state.log_rows else "—")

# --- Footer ---
st.markdown(
    '<div class="footer-brand">'
    'Adaptive Collision Risk Prediction System · TTC Dashboard v2.0'
    '</div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Auto-refresh: pause briefly then trigger a rerun to fetch the next reading.
# ---------------------------------------------------------------------------
if auto_refresh:
    time.sleep(REFRESH_SEC)
    st.rerun()