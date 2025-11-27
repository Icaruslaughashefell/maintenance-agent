import streamlit as st
import plotly.express as px
import pandas as pd

# ---------------------
# Page Config
# ---------------------
st.set_page_config(
    page_title="Factory Machine Maintenance Dashboard",
    layout="wide"
)

# ---------------------
# Header
# ---------------------
st.markdown(
    """
    <h1 style='color:#007bff;'>
        🏭 Factory Machine Maintenance Overview
    </h1>
    <p>Data Status: Last Updated 2025-11-27 19:30 UTC</p>
    """,
    unsafe_allow_html=True
)

# ---------------------
# KPI Cards Layout
# ---------------------
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div style='padding:20px; background:white; border-radius:10px; border-left:6px solid #28a745; box-shadow:0 2px 4px rgba(0,0,0,0.1);'>
        <h4>Success Rate (Uptime)</h4>
        <h1 style='color:#28a745;'>97.4%</h1>
        <p>Target: 98%</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style='padding:20px; background:white; border-radius:10px; border-left:6px solid #ffc107; box-shadow:0 2px 4px rgba(0,0,0,0.1);'>
        <h4>Avg. Latency</h4>
        <h1 style='color:#ffc107;'>285 ms</h1>
        <p>5% slower than last week</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style='padding:20px; background:white; border-radius:10px; border-left:6px solid #dc3545; box-shadow:0 2px 4px rgba(0,0,0,0.1);'>
        <h4>Critical Defects (Last 24h)</h4>
        <h1 style='color:#dc3545;'>3</h1>
        <p>Requires immediate action</p>
    </div>
    """, unsafe_allow_html=True)

st.write("")  # spacing

# ---------------------
# Charts Section
# ---------------------
left, right = st.columns(2)

# Fake Data for charts
df_defects = pd.DataFrame({
    "Defect": ["Bearing Wear", "Misalignment", "Overheating"],
    "Count": [45, 30, 15]
})

df_latency = pd.DataFrame({
    "Day": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    "Latency(ms)": [240, 260, 300, 280, 310, 295, 285]
})

with left:
    st.subheader("📉 Defect Type Frequency")
    fig1 = px.bar(df_defects, x="Defect", y="Count", color="Defect",
                  template="simple_white")
    st.plotly_chart(fig1, use_container_width=True)

with right:
    st.subheader("⏱ Latency Trend (Past 7 Days)")
    fig2 = px.line(df_latency, x="Day", y="Latency(ms)",
                   markers=True, template="simple_white")
    st.plotly_chart(fig2, use_container_width=True)

# ---------------------
# Logs Table
# ---------------------
st.subheader("🛠 Recent Maintenance Logs")

df_logs = pd.DataFrame({
    "Timestamp": [
        "2025-11-27 18:20", "2025-11-27 17:10", "2025-11-27 15:45"
    ],
    "Machine": ["M-12", "M-03", "M-07"],
    "Issue": ["Overheating", "Bearing Wear", "Misalignment"],
    "Status": ["Fixed", "In Progress", "Pending Check"]
})

st.dataframe(df_logs, use_container_width=True)
