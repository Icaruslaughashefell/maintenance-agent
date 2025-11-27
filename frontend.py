"""
maintenance_agent_frontend.py
=============================================
Streamlit UI สำหรับ Maintenance Agent + Dashboard

- Mode = "Maintenance Agent":
    * Upload รูป
    * พิมพ์คำถามเสริม (optional)
    * ระบุ client_id
    * ส่งไป backend /analyze
    * Backend จะเซฟ log ลง SQLite + รูปที่ฝั่ง server

- Mode = "Dashboard":
    * อ่านฐานข้อมูลเดียวกับ backend: logs/maintenance_logs.db
    * แสดง KPI, กราฟ defect, กราฟ latency, และตาราง log ล่าสุด
"""

import base64
import time
import sqlite3
from pathlib import Path

import requests
import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------------
# Config
# ---------------------
DEFAULT_API_URL = "http://127.0.0.1:8000/analyze"

# ให้ชี้ไปที่โฟลเดอร์ logs เดียวกับ backend
ROOT_DIR = Path(__file__).parent
DB_PATH = ROOT_DIR / "logs" / "maintenance_logs.db"


st.set_page_config(
    page_title="Maintenance Agent & Dashboard",
    layout="wide",
)

# ---------------------
# Helper: โหลด logs จาก SQLite
# ---------------------
def load_logs_from_db(db_path: Path) -> pd.DataFrame:
    """อ่าน log จาก SQLite ถ้าไม่มีไฟล์เลยจะคืน DataFrame ว่าง"""
    if not db_path.exists():
        return pd.DataFrame()

    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query("SELECT * FROM logs ORDER BY ts DESC", conn)
    finally:
        conn.close()

    if "ts" in df.columns:
        df["ts"] = pd.to_datetime(df["ts"], errors="coerce")

    return df

# ---------------------
# Sidebar config
# ---------------------
st.sidebar.header("Settings")

mode = st.sidebar.radio(
    "Mode",
    options=["Dashboard", "Maintenance Agent"],
    index=1,  # default = Agent
    help="เลือกเปิดหน้า Dashboard หรือหน้า Maintenance Agent",
)

api_url = st.sidebar.text_input("Backend API URL", DEFAULT_API_URL)

client_id = st.sidebar.text_input(
    "Client ID (ชื่อเครื่อง/ผู้ใช้งาน)",
    value="client-1",
    help="ใช้สำหรับระบุว่า log นี้มาจากเครื่องไหน จะถูกเก็บใน DB ของ backend",
)

# =====================================================================
# MODE 1: DASHBOARD (ดึงข้อมูลจริงจาก maintenance_logs.db)
# =====================================================================
def render_dashboard():
    st.markdown(
        "<h1 style='color:#007bff;'>🏭 Factory Machine Maintenance Dashboard</h1>",
        unsafe_allow_html=True,
    )

    df = load_logs_from_db(DB_PATH)

    if df.empty:
        st.info(
            "ยังไม่มีข้อมูลในฐาน `logs/maintenance_logs.db` "
            "ลองให้ Maintenance Agent วิเคราะห์รูปอย่างน้อย 1 ครั้งก่อนนะครับ 🙂"
        )
        return

    # --------------------- KPI ---------------------
    total = len(df)

    if "status" in df.columns:
        ok_count = (df["status"] == "OK").sum()
        ng_count = (df["status"] == "NG").sum()
    else:
        ok_count = ng_count = None

    if total > 0 and ok_count is not None:
        uptime = ok_count / total * 100.0
    else:
        uptime = None

    if "latency_ms" in df.columns and not df["latency_ms"].isna().all():
        avg_latency = df["latency_ms"].mean()
    else:
        avg_latency = None

    critical_defects = ng_count if ng_count is not None else None

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            f"""
            <div style='padding:20px; background:white; border-radius:10px;
                        border-left:6px solid #28a745; box-shadow:0 2px 4px rgba(0,0,0,0.1);'>
                <h4>Success Rate (Uptime)</h4>
                <h1 style='color:#28a745;'>{uptime:.1f}%</h1>
                <p>Total checks: {total}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        latency_str = f"{avg_latency:.0f} ms" if avg_latency is not None else "N/A"
        st.markdown(
            f"""
            <div style='padding:20px; background:white; border-radius:10px;
                        border-left:6px solid #ffc107; box-shadow:0 2px 4px rgba(0,0,0,0.1);'>
                <h4>Avg. Backend Latency</h4>
                <h1 style='color:#ffc107;'>{latency_str}</h1>
                <p>เฉลี่ยจากทุกการเรียก /analyze</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        critical_str = critical_defects if critical_defects is not None else "N/A"
        st.markdown(
            f"""
            <div style='padding:20px; background:white; border-radius:10px;
                        border-left:6px solid #dc3545; box-shadow:0 2px 4px rgba(0,0,0,0.1);'>
                <h4>Critical Defects (NG)</h4>
                <h1 style='color:#dc3545;'>{critical_str}</h1>
                <p>นับเฉพาะ status = NG</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")

    # --------------------- Charts ---------------------
    left, right = st.columns(2)

    # Defect frequency
    # แทนทั้งบล็อกเดิมส่วนสร้าง defect_counts ด้วยอันนี้
    if "defect_type" in df.columns:
        defect_counts = (
            df["defect_type"]
            .fillna("unknown")
            .value_counts()                # ได้ Series index=defect, value=count
            .rename_axis("Defect")         # ตั้งชื่อ index
            .reset_index(name="Count")     # index -> คอลัมน์ Defect, value -> Count
        )
    else:
        defect_counts = pd.DataFrame(columns=["Defect", "Count"])


    with left:
        st.subheader("📉 Defect Type Frequency")
        if defect_counts.empty:
            st.write("ยังไม่มีข้อมูล defect_type")
        else:
            fig1 = px.bar(
                defect_counts,
                x="Defect",
                y="Count",
                color="Defect",
                template="simple_white",
            )
            st.plotly_chart(fig1, use_container_width=True)

    # Latency trend (โดยเวลา)
    with right:
        st.subheader("⏱ Latency Trend (by time)")
        if "ts" in df.columns and "latency_ms" in df.columns:
            df_lat = (
                df.dropna(subset=["ts"])
                .sort_values("ts")
                .tail(200)  # limit เพื่อไม่ให้กราฟแน่นเกิน
            )
            fig2 = px.line(
                df_lat,
                x="ts",
                y="latency_ms",
                markers=True,
                template="simple_white",
                labels={"ts": "Timestamp", "latency_ms": "Latency (ms)"},
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.write("ยังไม่มีข้อมูล timestamp หรือ latency_ms")

    # --------------------- Logs Table ---------------------
    st.subheader("🛠 Recent Maintenance Logs")

    cols_show = []
    for c in ["ts", "client_id", "defect_type", "status", "confidence", "latency_ms"]:
        if c in df.columns:
            cols_show.append(c)

    if cols_show:
        st.dataframe(df[cols_show].head(200), use_container_width=True)
    else:
        st.write("ไม่พบคอลัมน์ที่ต้องการในตาราง logs")


# =====================================================================
# MODE 2: MAINTENANCE AGENT (เหมือนเวอร์ชันเดิม)
# =====================================================================
def render_agent():
    st.title("🛠 Maintenance Agent – Vision + RAG Demo")

    col_left, col_right = st.columns([1, 1])

    # ----------- ฝั่งซ้าย: อัปโหลดรูป + คำถาม -----------
    with col_left:
        st.subheader("1) Upload Machine Image")
        uploaded_file = st.file_uploader(
            "Choose an image", type=["jpg", "jpeg", "png"]
        )

        user_question = st.text_area(
            "Optional question (e.g. specific symptom / sound / vibration)",
            help="ข้อความนี้จะถูกส่งไปเสริม prompt ให้ VLM",
        )

        file_bytes = None
        if uploaded_file is not None:
            # เก็บ bytes ไว้ส่งให้ backend + แสดง preview
            file_bytes = uploaded_file.read()
            st.image(uploaded_file, caption="Preview", use_container_width=True)

        run_button = st.button("Analyze", type="primary")

    # ----------- ฝั่งขวา: แสดงผลจาก backend -----------
    with col_right:
        st.subheader("2) Result")

        if run_button:
            if file_bytes is None:
                st.warning("กรุณาอัปโหลดรูปก่อน")
            else:
                # แปลงรูปเป็น base64
                img_b64 = base64.b64encode(file_bytes).decode("utf-8")

                payload = {
                    "image_base64": img_b64,
                    "question": user_question or None,
                    "client_id": client_id or None,
                }

                try:
                    # เรียก backend แบบเดียวกับ maintenance_agent_frontend.py
                    with st.spinner("Analyzing..."):
                        t0 = time.time()
                        resp = requests.post(api_url, json=payload, timeout=60)
                        roundtrip_ms = (time.time() - t0) * 1000

                    if resp.status_code != 200:
                        st.error(f"API error: {resp.status_code} {resp.text}")
                        return

                    data = resp.json()

                    status = data["status"]
                    defect_type = data["defect_type"]
                    confidence = data["confidence"]
                    latency_ms = data.get("latency_ms", 0.0)

                    st.markdown(f"**Status:** `{status}`")
                    st.markdown(f"**Defect Type:** `{defect_type}`")
                    st.markdown(f"**Confidence:** `{confidence:.2f}`")
                    st.markdown(f"**Backend Latency:** `{latency_ms:.1f} ms`")
                    st.markdown(f"**Total Roundtrip:** `{roundtrip_ms:.1f} ms`")

                    st.markdown("### Action Recommended")
                    st.write(data["action_recommended"])

                    st.markdown("### RAG Sources")
                    if data["rag_sources"]:
                        for src in data["rag_sources"]:
                            st.markdown(
                                f"- **{src['manual_name']} p.{src['page']}** "
                                f"(score={src['score']:.2f})\n\n"
                                f"  > {src['snippet'][:300]}..."
                            )
                    else:
                        st.write("No RAG sources found.")

                    st.markdown("### Raw JSON")
                    st.json(data)

                except Exception as e:
                    st.error(f"Request failed: {e}")



# ---------------------
# Main switch by mode
# ---------------------
if mode == "Dashboard":
    render_dashboard()
else:
    render_agent()