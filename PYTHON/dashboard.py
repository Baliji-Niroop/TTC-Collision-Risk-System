"""
TTC Collision Risk Monitoring Dashboard
Adaptive Collision Risk Prediction System
-----------------------------------------
Modes:
  • Simulator    – smooth physics-based synthetic data (no hardware needed)
  • Live Log     – reads last line from LOGS/live_data.txt
  • ESP32 Serial – reads directly from USB serial (requires pyserial)

Run:
    pip install streamlit pandas numpy
    streamlit run dashboard.py
"""

import time
import math
import random
from pathlib import Path

import pandas as pd
import streamlit as st

# ──────────────────────────────────────────────────
# PATH CONFIG
# ──────────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parent
ROOT_DIR   = BASE_DIR.parent
MODEL_PATH = ROOT_DIR / "MODELS" / "ml_model.pkl"
DATA_PATH  = ROOT_DIR / "LOGS"   / "live_data.txt"

# ──────────────────────────────────────────────────
# CONSTANTS
# ──────────────────────────────────────────────────
MAX_POINTS  = 120
REFRESH_SEC = 0.6

RISK_LABELS = {0: "SAFE", 1: "WARNING", 2: "CRITICAL"}
RISK_COLORS = {
    0: ("✅ SAFE",     "#1a7a2e"),
    1: ("⚠️ WARNING",  "#b36b00"),
    2: ("🚨 CRITICAL", "#b71c1c"),
}

# ──────────────────────────────────────────────────
# PAGE CONFIG  ← must be the very first Streamlit call
# ──────────────────────────────────────────────────
st.set_page_config(
    page_title="TTC Dashboard",
    layout="wide",
    page_icon="🚗",
)

# ──────────────────────────────────────────────────
# OPTIONAL IMPORTS  (pyserial, joblib)
# ──────────────────────────────────────────────────
try:
    import serial
    import serial.tools.list_ports
    _SERIAL_OK = True
except ImportError:
    _SERIAL_OK = False


@st.cache_resource(show_spinner=False)
def _load_model():
    try:
        import joblib
        if MODEL_PATH.exists():
            return joblib.load(MODEL_PATH)
    except Exception:
        pass
    return None


model = _load_model()

# ──────────────────────────────────────────────────
# SESSION STATE
# ──────────────────────────────────────────────────
_STATE_DEFAULTS = {
    "buffer":         [],
    "min_ttc":        99.0,
    "critical_count": 0,
    "warning_count":  0,
    "session_start":  time.time(),
    "log_rows":       [],
    "sim_d":          8.0,   # simulator: distance in metres
    "sim_v":          1.0,   # simulator: velocity in m/s
    "sim_t":          0,     # simulator: tick counter
}
for _k, _v in _STATE_DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ──────────────────────────────────────────────────
# SIMULATOR  – smooth sine-wave approach / retreat
# ──────────────────────────────────────────────────
def simulate_step() -> dict:
    dt = REFRESH_SEC
    d  = st.session_state.sim_d
    v  = st.session_state.sim_v

    st.session_state.sim_t += 1
    t = st.session_state.sim_t

    # target velocity: slow sine oscillation so TTC visits all 3 zones
    target_v = 3.5 * math.sin(t * 0.07) + random.gauss(0, 0.1)
    v += (target_v - v) * 0.2                # soft follow
    v  = max(-2.0, min(v, 8.0))

    d -= v * dt
    if d < 0.3:                              # collision → reset
        d = random.uniform(6.0, 10.0)
        v = random.uniform(0.5, 2.5)
    if d > 15.0:                             # too far → nudge in
        v = max(v, 0.5)

    st.session_state.sim_d = d
    st.session_state.sim_v = v

    v_close   = max(v, 0.0)
    ttc_basic = (d / v_close) if v_close > 0.1 else 99.0
    ttc_basic = round(min(ttc_basic, 99.0), 2)

    a_decel   = 5.0
    disc      = v_close ** 2 + 2 * a_decel * d
    ttc_ext   = (-v_close + math.sqrt(max(disc, 0.0))) / a_decel
    ttc_ext   = round(min(ttc_ext, 99.0), 2)

    risk = 0 if ttc_basic > 3.0 else (1 if ttc_basic > 1.5 else 2)

    return {
        "distance_cm": round(d * 100, 1),
        "speed_kmh":   round(abs(v) * 3.6, 1),
        "ttc_basic":   ttc_basic,
        "ttc_ext":     ttc_ext,
        "risk_phys":   risk,
        "confidence":  round(random.uniform(0.76, 0.99), 2),
    }

# ──────────────────────────────────────────────────
# CSV PARSER
# ──────────────────────────────────────────────────
def parse_csv_line(line: str):
    """
    Parse a 7-field CSV line.
    Format: timestamp_ms, distance_cm, speed_kmh, ttc_basic, ttc_ext, risk_class, confidence
    Returns dict or None on any failure.
    """
    try:
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 7:
            return None
        return {
            "distance_cm": float(parts[1]),
            "speed_kmh":   float(parts[2]),
            "ttc_basic":   float(parts[3]),
            "ttc_ext":     float(parts[4]),
            "risk_phys":   int(float(parts[5])),
            "confidence":  float(parts[6]),
        }
    except Exception:
        return None

# ──────────────────────────────────────────────────
# LOG FILE READER
# ──────────────────────────────────────────────────
def read_log_file():
    try:
        lines = DATA_PATH.read_text(encoding="utf-8").splitlines()
        for line in reversed(lines):
            if line.strip():
                return parse_csv_line(line.strip())
    except Exception:
        pass
    return None

# ──────────────────────────────────────────────────
# SERIAL READER  (connection cached for the session)
# ──────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def _open_serial(port: str):
    try:
        return serial.Serial(port, 115200, timeout=1)
    except Exception:
        return None


def read_serial(port: str):
    try:
        ser = _open_serial(port)
        if ser is None or not ser.is_open:
            return None
        raw = ser.readline().decode("utf-8", errors="ignore").strip()
        return parse_csv_line(raw)
    except Exception:
        return None

# ──────────────────────────────────────────────────
# ML PREDICTION
# ──────────────────────────────────────────────────
def ml_predict(row: dict) -> int:
    if model is None:
        return row["risk_phys"]
    try:
        d_m       = row["distance_cm"] / 100.0
        spd       = row["speed_kmh"]
        ttc       = row["ttc_basic"]
        close_vel = d_m / max(ttc, 0.1)
        features  = pd.DataFrame(
            [[spd, d_m, close_vel, ttc, 0]],
            columns=["speed", "distance", "closing_vel", "ttc", "road"],
        )
        return int(model.predict(features)[0])
    except Exception:
        return row["risk_phys"]

# ──────────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────────
st.sidebar.title("⚙️ Configuration")

_mode_opts = ["Simulator"]
if DATA_PATH.exists():
    _mode_opts.append("Live Log")
if _SERIAL_OK:
    _mode_opts.append("ESP32 Serial")

mode = st.sidebar.radio("Data Source", _mode_opts)

serial_port = None
if mode == "ESP32 Serial" and _SERIAL_OK:
    _ports = [p.device for p in serial.tools.list_ports.comports()]
    if _ports:
        serial_port = st.sidebar.selectbox("COM Port", _ports)
    else:
        st.sidebar.error("No serial ports found. Check USB cable.")

st.sidebar.markdown("---")
st.sidebar.markdown(f"**ML Model:** {'✅ Loaded' if model else '❌ Not found — using physics'}")
st.sidebar.markdown(f"**pyserial:** {'✅ Available' if _SERIAL_OK else '❌ Not installed'}")

if st.sidebar.button("🔄 Reset Session"):
    for _k in list(_STATE_DEFAULTS.keys()):
        if _k in st.session_state:
            del st.session_state[_k]
    st.rerun()

# ──────────────────────────────────────────────────
# FETCH DATA
# ──────────────────────────────────────────────────
if mode == "Simulator":
    row = simulate_step()

elif mode == "Live Log":
    row = read_log_file()
    if row is None:
        st.warning("⏳ Waiting for data in LOGS/live_data.txt …")
        time.sleep(1)
        st.rerun()

else:  # ESP32 Serial
    if serial_port is None:
        st.error("❌ No serial port selected.")
        st.stop()
    row = read_serial(serial_port)
    if row is None:
        st.warning("⏳ Waiting for ESP32 serial data …")
        time.sleep(1)
        st.rerun()

# ──────────────────────────────────────────────────
# PROCESS ROW
# ──────────────────────────────────────────────────
risk  = ml_predict(row)
ttc_b = row["ttc_basic"]

# Update session stats
if ttc_b < st.session_state.min_ttc:
    st.session_state.min_ttc = ttc_b
if risk == 2:
    st.session_state.critical_count += 1
if risk == 1:
    st.session_state.warning_count  += 1

# Rolling chart buffer
st.session_state.buffer.append({
    "TTC Basic (s)": ttc_b,
    "TTC Ext (s)":   row["ttc_ext"],
    "Distance (m)":  round(row["distance_cm"] / 100, 2),
    "Speed (km/h)":  row["speed_kmh"],
})
if len(st.session_state.buffer) > MAX_POINTS:
    st.session_state.buffer.pop(0)

df = pd.DataFrame(st.session_state.buffer)

# Event log
st.session_state.log_rows.append({
    "time":          time.strftime("%H:%M:%S"),
    "ttc_basic_s":   ttc_b,
    "ttc_ext_s":     row["ttc_ext"],
    "distance_m":    round(row["distance_cm"] / 100, 3),
    "speed_kmh":     row["speed_kmh"],
    "risk":          RISK_LABELS[risk],
    "confidence_%":  round(row["confidence"] * 100, 1),
})

# ──────────────────────────────────────────────────
# ── RENDER UI ──
# ──────────────────────────────────────────────────
st.title("🚗 TTC Collision Risk Dashboard")
st.caption(f"Adaptive Collision Risk Prediction System  ·  {time.strftime('%H:%M:%S')}")

# Risk Banner
label, color = RISK_COLORS[risk]
st.markdown(
    f'<div style="background:{color};color:white;text-align:center;'
    f'padding:16px;border-radius:8px;font-size:2rem;font-weight:700;">'
    f'{label}</div>',
    unsafe_allow_html=True,
)
st.markdown("")

# KPI Row 1
c1, c2, c3, c4 = st.columns(4)
prev_ttc = df["TTC Basic (s)"].iloc[-2] if len(df) >= 2 else None
c1.metric("⏱ TTC Basic",    f"{ttc_b:.2f} s",
          delta=f"{ttc_b - prev_ttc:.2f} s" if prev_ttc is not None else None)
c2.metric("⏱ TTC Extended", f"{row['ttc_ext']:.2f} s")
c3.metric("📏 Distance",    f"{row['distance_cm'] / 100:.2f} m")
c4.metric("🚀 Speed",       f"{row['speed_kmh']:.1f} km/h")

st.markdown("---")

# KPI Row 2
c5, c6, c7, c8 = st.columns(4)
c5.metric("🎯 Confidence",        f"{row['confidence'] * 100:.0f}%")
c6.metric("📉 Min TTC (session)", f"{st.session_state.min_ttc:.2f} s")
c7.metric("🚨 Critical Events",   st.session_state.critical_count)
c8.metric("⚠️ Warning Events",    st.session_state.warning_count)

st.markdown("---")

# Charts
col_l, col_r = st.columns(2)
with col_l:
    st.subheader("TTC Trend")
    if len(df) >= 2:
        st.line_chart(df[["TTC Basic (s)", "TTC Ext (s)"]], height=250)
    else:
        st.info("Collecting data…")

with col_r:
    st.subheader("Distance & Speed Trend")
    if len(df) >= 2:
        st.line_chart(df[["Distance (m)", "Speed (km/h)"]], height=250)
    else:
        st.info("Collecting data…")

st.markdown("---")

# Risk Zone Reference
st.subheader("Risk Zone Reference")
z1, z2, z3 = st.columns(3)
z1.success("✅ SAFE — TTC > 3.0 s")
z2.warning("⚠️ WARNING — 1.5 s to 3.0 s")
z3.error("🚨 CRITICAL — TTC < 1.5 s")

st.markdown("---")

# Event Log + Export
st.subheader("📋 Event Log (last 30 rows)")
if st.session_state.log_rows:
    log_df = pd.DataFrame(st.session_state.log_rows).tail(30)
    st.dataframe(log_df, use_container_width=True, height=240)
    csv_bytes = pd.DataFrame(st.session_state.log_rows).to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download Full Session CSV",
        data=csv_bytes,
        file_name=f"ttc_session_{int(time.time())}.csv",
        mime="text/csv",
    )
else:
    st.info("No events yet.")

st.markdown("---")

# Session Summary
elapsed   = int(time.time() - st.session_state.session_start)
h, rem    = divmod(elapsed, 3600)
m_t, s_t  = divmod(rem, 60)
total     = max(len(st.session_state.log_rows), 1)
safe_pct  = round(
    sum(1 for r in st.session_state.log_rows if r["risk"] == "SAFE") / total * 100
)

st.subheader("📊 Session Summary")
s1, s2, s3, s4 = st.columns(4)
s1.metric("⏰ Session Duration", f"{h:02d}:{m_t:02d}:{s_t:02d}")
s2.metric("📦 Total Readings",   total)
s3.metric("✅ % Time SAFE",      f"{safe_pct}%")
s4.metric("📈 Mean TTC",
          f"{df['TTC Basic (s)'].mean():.2f} s" if len(df) > 0 else "—")

# ──────────────────────────────────────────────────
# AUTO REFRESH  (no third-party library needed)
# ──────────────────────────────────────────────────
time.sleep(REFRESH_SEC)
st.rerun()