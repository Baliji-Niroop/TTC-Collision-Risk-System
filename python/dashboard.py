#!/usr/bin/env python3
"""
@file dashboard.py
@brief Real-time TTC monitoring dashboard using Streamlit

Professional dashboard for monitoring collision detection system:
- Real-time TTC gauge with threshold indicators
- Distance and velocity time-series charts
- Risk state transitions and event log
- Session statistics (min TTC, critical count, time per risk level)
- CSV export for analysis
- Serial port selector and configuration controls

Features:
- Auto-connects to ESP32 via Serial
- Parses CSV telemetry stream
- Live update every 0.5 seconds
- Requires: streamlit, plotly, pandas, pyserial
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import serial
import serial.tools.list_ports
from datetime import datetime
from collections import deque
import numpy as np

# ===== PAGE CONFIGURATION =====
st.set_page_config(
    page_title="TTC Collision Monitor",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===== SESSION STATE INITIALIZATION =====
if 'serial_conn' not in st.session_state:
    st.session_state.serial_conn = None

if 'data_buffer' not in st.session_state:
    st.session_state.data_buffer = deque(maxlen=600)  # 600 samples = 60 seconds at 10Hz

if 'risk_events' not in st.session_state:
    st.session_state.risk_events = []

if 'connected' not in st.session_state:
    st.session_state.connected = False

# ===== HELPER FUNCTIONS =====
def get_available_ports():
    """Return list of available serial ports"""
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports] if ports else []

def establish_connection(port, baudrate=115200):
    """Establish serial connection to ESP32"""
    try:
        if st.session_state.serial_conn:
            st.session_state.serial_conn.close()
        
        st.session_state.serial_conn = serial.Serial(port, baudrate, timeout=1)
        st.session_state.connected = True
        return True
    except Exception as e:
        st.error(f"Failed to connect: {e}")
        st.session_state.connected = False
        return False

def parse_csv_line(line):
    """Parse single CSV line from telemetry stream
    
    Format: timestamp_ms,d_fused_cm,d_filtered_cm,v_closing_ms,ttc_basic_s,
            ttc_ext_s,risk_class,confidence,loop_time_us
    """
    try:
        fields = line.strip().split(',')
        if len(fields) < 9:
            return None
        
        return {
            'timestamp_ms': int(fields[0]),
            'd_fused_cm': float(fields[1]),
            'd_filtered_cm': float(fields[2]),
            'v_closing_ms': float(fields[3]),
            'ttc_basic_s': float(fields[4]),
            'ttc_ext_s': float(fields[5]),
            'risk_class': int(fields[6]),  # 0=SAFE, 1=WARNING, 2=CRITICAL
            'confidence': float(fields[7]),
            'loop_time_us': int(fields[8])
        }
    except (ValueError, IndexError):
        return None

def risk_to_string(risk_class):
    """Convert risk class number to string"""
    risk_names = {0: "SAFE", 1: "WARNING", 2: "CRITICAL"}
    return risk_names.get(risk_class, "UNKNOWN")

def risk_to_color(risk_class):
    """Get color for risk level"""
    colors = {0: "green", 1: "orange", 2: "red"}
    return colors.get(risk_class, "gray")

# ===== SIDEBAR: CONFIGURATION =====
st.sidebar.title("⚙️ Configuration")

# Serial port selection
available_ports = get_available_ports()
if not available_ports:
    st.sidebar.warning("No serial ports detected")
    port_select = None
else:
    port_select = st.sidebar.selectbox(
        "Serial Port",
        options=available_ports,
        help="Select ESP32 COM port"
    )

# Connect/Disconnect button
col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("🔗 Connect"):
        if port_select:
            establish_connection(port_select)
            st.sidebar.success("Connected!" if st.session_state.connected else "Failed")

with col2:
    if st.button("🔌 Disconnect"):
        if st.session_state.serial_conn:
            st.session_state.serial_conn.close()
            st.session_state.connected = False
        st.sidebar.info("Disconnected")

# Connection status
if st.session_state.connected:
    st.sidebar.success("✅ Connected")
else:
    st.sidebar.error("❌ Not Connected")

# Data refresh rate
refresh_interval = st.sidebar.slider(
    "Refresh interval (seconds)",
    min_value=0.1,
    max_value=5.0,
    value=0.5,
    step=0.1
)

# ===== MAIN DASHBOARD =====
st.title("🚗 TTC Collision Detection Monitor")

if not st.session_state.connected:
    st.info("👉 Select a serial port and click Connect to start monitoring")
else:
    # Read latest data from serial
    if st.session_state.serial_conn and st.session_state.serial_conn.in_waiting > 0:
        try:
            line = st.session_state.serial_conn.readline().decode('utf-8', errors='ignore')
            data = parse_csv_line(line)
            
            if data:
                st.session_state.data_buffer.append(data)
                
                # Track risk transitions for event log
                if len(st.session_state.data_buffer) > 0:
                    current_risk = data['risk_class']
                    if len(st.session_state.risk_events) == 0 or st.session_state.risk_events[-1][0] != current_risk:
                        st.session_state.risk_events.append((current_risk, datetime.now()))
        except Exception as e:
            pass  # Silently skip malformed lines
    
    # Display current status
    if len(st.session_state.data_buffer) > 0:
        latest = st.session_state.data_buffer[-1]
        
        # Top status row with key metrics
        st.markdown("---")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                "TTC Basic",
                f"{latest['ttc_basic_s']:.2f}s",
                delta=None,
                delta_color="off"
            )
        
        with col2:
            st.metric(
                "Distance",
                f"{latest['d_filtered_cm']:.1f}cm",
                delta=None
            )
        
        with col3:
            st.metric(
                "Velocity",
                f"{latest['v_closing_ms']:.2f}m/s",
                delta=None
            )
        
        with col4:
            st.metric(
                "Confidence",
                f"{latest['confidence']:.0%}",
                delta=None
            )
        
        with col5:
            risk_str = risk_to_string(latest['risk_class'])
            st.metric(
                "Risk Level",
                risk_str,
                delta=None,
                delta_color="off"
            )
        
        st.markdown("---")
        
        # ===== TTC GAUGE =====
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Create gauge chart
            fig_gauge = go.Figure(data=[
                go.Indicator(
                    mode="gauge+number+delta",
                    value=latest['ttc_basic_s'],
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "Time-to-Collision (seconds)"},
                    delta={'reference': 3.0},
                    gauge={
                        'axis': {'range': [0, 5]},
                        'bar': {'color': "darkblue"},
                        'steps': [
                            {'range': [0, 1.5], 'color': "lightcoral"},
                            {'range': [1.5, 3.0], 'color': "lightyellow"},
                            {'range': [3.0, 5], 'color': "lightgreen"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 1.5
                        }
                    }
                )
            ])
            fig_gauge.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig_gauge, use_container_width=True)
        
        with col2:
            # Risk indicator box
            risk_color = risk_to_color(latest['risk_class'])
            st.markdown(f"""
            ### Risk Status
            <div style='padding: 20px; border-radius: 10px; background-color: {risk_color}; 
                        color: white; font-size: 24px; text-align: center; font-weight: bold;'>
                {risk_to_string(latest['risk_class'])}
            </div>
            """, unsafe_allow_html=True)
            
            # Thresholds info
            st.markdown("""
            **Thresholds:**
            - 🟢 **SAFE**: > 3.0s
            - 🟡 **WARNING**: 1.5-3.0s
            - 🔴 **CRITICAL**: < 1.5s
            """)
        
        st.markdown("---")
        
        # ===== TIME SERIES CHARTS =====
        if len(st.session_state.data_buffer) > 1:
            df = pd.DataFrame(list(st.session_state.data_buffer))
            df['timestamp'] = pd.to_datetime(df['timestamp_ms'], unit='ms')
            df['risk_str'] = df['risk_class'].apply(risk_to_string)
            
            # TTC and Distance chart
            col1, col2 = st.columns(2)
            
            with col1:
                fig_ttc = go.Figure()
                fig_ttc.add_trace(go.Scatter(
                    x=df['timestamp'],
                    y=df['ttc_basic_s'],
                    mode='lines',
                    name='TTC Basic',
                    line=dict(color='blue', width=2)
                ))
                fig_ttc.add_hline(y=3.0, line_dash="dash", line_color="green", annotation_text="Safe Threshold")
                fig_ttc.add_hline(y=1.5, line_dash="dash", line_color="red", annotation_text="Critical Threshold")
                fig_ttc.update_layout(
                    title="Time-to-Collision Over Time",
                    xaxis_title="Time",
                    yaxis_title="TTC (seconds)",
                    hovermode='x unified',
                    height=350
                )
                st.plotly_chart(fig_ttc, use_container_width=True)
            
            with col2:
                fig_dist = go.Figure()
                fig_dist.add_trace(go.Scatter(
                    x=df['timestamp'],
                    y=df['d_filtered_cm'],
                    mode='lines',
                    name='Distance (filtered)',
                    line=dict(color='darkgreen', width=2)
                ))
                fig_dist.add_trace(go.Scatter(
                    x=df['timestamp'],
                    y=df['d_fused_cm'],
                    mode='lines',
                    name='Distance (fused)',
                    line=dict(color='lightgreen', width=1, dash='dot'),
                    opacity=0.7
                ))
                fig_dist.update_layout(
                    title="Distance Measurements",
                    xaxis_title="Time",
                    yaxis_title="Distance (cm)",
                    hovermode='x unified',
                    height=350
                )
                st.plotly_chart(fig_dist, use_container_width=True)
            
            # Velocity chart
            fig_vel = go.Figure()
            fig_vel.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df['v_closing_ms'],
                mode='lines',
                name='Closing Velocity',
                line=dict(color='purple', width=2),
                fill='tozeroy'
            ))
            fig_vel.update_layout(
                title="Closing Velocity",
                xaxis_title="Time",
                yaxis_title="Velocity (m/s)",
                hovermode='x unified',
                height=300
            )
            st.plotly_chart(fig_vel, use_container_width=True)
        
        st.markdown("---")
        
        # ===== SESSION STATISTICS =====
        st.subheader("📊 Session Statistics")
        
        if len(st.session_state.data_buffer) > 0:
            df = pd.DataFrame(list(st.session_state.data_buffer))
            
            stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
            
            with stat_col1:
                min_ttc = df['ttc_basic_s'].min()
                st.metric("Minimum TTC", f"{min_ttc:.2f}s")
            
            with stat_col2:
                critical_count = (df['risk_class'] == 2).sum()
                st.metric("Critical Events", f"{critical_count}")
            
            with stat_col3:
                avg_confidence = df['confidence'].mean()
                st.metric("Avg Confidence", f"{avg_confidence:.0%}")
            
            with stat_col4:
                measurements = len(df)
                st.metric("Measurements", f"{measurements}")
            
            # Risk distribution pie chart
            risk_dist = df['risk_class'].value_counts().sort_index()
            risk_labels = [risk_to_string(i) for i in risk_dist.index]
            
            fig_pie = px.pie(
                values=risk_dist.values,
                names=risk_labels,
                title="Risk Distribution",
                color_discrete_map={'SAFE': 'green', 'WARNING': 'orange', 'CRITICAL': 'red'}
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        st.markdown("---")
        
        # ===== EVENT LOG =====
        st.subheader("📋 Recent Events")
        
        if len(st.session_state.risk_events) > 0:
            # Show last 10 events
            events_df = pd.DataFrame(
                [(risk_to_string(r), t.strftime("%H:%M:%S.%f")[:-3]) 
                 for r, t in st.session_state.risk_events[-10:]],
                columns=['Risk Level', 'Time']
            )
            st.dataframe(events_df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # ===== DATA EXPORT =====
        st.subheader("💾 Export Data")
        
        if len(st.session_state.data_buffer) > 0:
            df = pd.DataFrame(list(st.session_state.data_buffer))
            csv = df.to_csv(index=False)
            
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"ttc_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        # Auto-refresh
        import time
        time.sleep(refresh_interval)
        st.rerun()
    else:
        st.info("Waiting for data from ESP32...")
