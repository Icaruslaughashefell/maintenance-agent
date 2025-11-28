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
from datetime import datetime, timedelta

# ---------------------
# Config
# ---------------------
# ---------------------
# Config
# ---------------------
DEFAULT_API_URL = "http://127.0.0.1:8000/analyze"

# ตำแหน่งไฟล์ DB บนเครื่องเซิร์ฟเวอร์ (ผ่าน Network)
SERVER_DB_PATH = Path(
    r"\\10.125.196.166\maintenance-agent-logs\maintenance_logs.db"
)

# fallback: กรณีรันบนเครื่อง server เอง หรือเข้า network share ไม่ได้
LOCAL_DB_PATH = Path("logs") / "maintenance_logs.db"

# เลือกใช้ SERVER_DB_PATH ถ้าเข้าถึงได้ ไม่งั้นใช้ LOCAL_DB_PATH
DB_PATH = SERVER_DB_PATH if SERVER_DB_PATH.exists() else LOCAL_DB_PATH



st.set_page_config(
    page_title="Maintenance Agent & Dashboard",
    layout="wide",
)

# ---------------------
# Helper: โหลด logs จาก SQLite
# ---------------------
def ensure_schema(db_path: Path) -> None:
    """แน่ใจว่า table logs มีคอลัมน์ resolved / resolved_ts"""
    if not db_path.exists():
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(logs)")
    cols = [row[1] for row in cur.fetchall()]

    if "resolved" not in cols:
        cur.execute("ALTER TABLE logs ADD COLUMN resolved INTEGER DEFAULT 0")

    if "resolved_ts" not in cols:
        cur.execute("ALTER TABLE logs ADD COLUMN resolved_ts TEXT")

    conn.commit()
    conn.close()


def load_logs_from_db(db_path: Path) -> pd.DataFrame:
    ...
    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query("SELECT * FROM logs ORDER BY ts DESC", conn)
    finally:
        conn.close()

    # --- แก้ตรงนี้ ---
    if "ts" in df.columns:
        # แปลงเป็น datetime ก่อน
        df["ts"] = pd.to_datetime(df["ts"], errors="coerce")

        # ถ้า ts เป็นแบบมี timezone (เช่น datetime64[ns, UTC]) ให้ตัด timezone ทิ้งให้เป็น naive
        if str(df["ts"].dtype).startswith("datetime64[ns, "):
            # เอา timezone ออก
            df["ts"] = df["ts"].dt.tz_convert(None)
    # ----------------

    # แปลง resolved ให้เป็น bool ตามเดิม
    if "resolved" not in df.columns:
        df["resolved"] = 0
    df["resolved"] = df["resolved"].fillna(0).astype(int).astype(bool)

    return df


def update_resolved_flags(db_path: Path, edited_df: pd.DataFrame) -> None:
    """เขียนค่า resolved / resolved_ts กลับเข้า SQLite ตามตารางที่แก้ใน data_editor"""
    if "id" not in edited_df.columns or "resolved" not in edited_df.columns:
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    now_iso = datetime.utcnow().isoformat()

    for _, row in edited_df.iterrows():
        _id = int(row["id"])
        res = bool(row["resolved"])
        if res:
            cur.execute(
                "UPDATE logs SET resolved = 1, resolved_ts = ? WHERE id = ?",
                (now_iso, _id),
            )
        else:
            cur.execute(
                "UPDATE logs SET resolved = 0, resolved_ts = NULL WHERE id = ?",
                (_id,),
            )

    conn.commit()
    conn.close()

# ---------------------
# Sidebar config
# ---------------------
st.sidebar.header("Settings")

mode = st.sidebar.radio(
    "Mode",
    options=["Dashboard", "Maintenance Agent"],
    index=0,
    help="เลือกเปิดหน้า Dashboard หรือหน้า Maintenance Agent",
)

api_url = st.sidebar.text_input("Backend API URL", DEFAULT_API_URL)

# 🔌 Dashboard DB path (ดึงจากเครื่องไหนก็ได้)
db_path_str = st.sidebar.text_input(
    "Dashboard DB path",
    value=str(DEFAULT_DB_PATH),
    help=(
        "ที่อยู่ของไฟล์ maintenance_logs.db\n"
        "ถ้ารันบนเครื่องอื่นให้ใส่ network path เช่น \\\\192.168.1.50\\maintenance-agent\\logs\\maintenance_logs.db"
    ),
)
db_path = Path(db_path_str)

# 👇 ทำเป็น dropdown ของหมายเลขเครื่อง
CLIENT_OPTIONS = ["001", "002", "003", "004", "005"]

client_id = st.sidebar.selectbox(
    "Client ID (ชื่อเครื่อง/ผู้ใช้งาน)",
    options=CLIENT_OPTIONS,
    index=0,
    help="ใช้สำหรับระบุว่า log นี้มาจากเครื่องไหน จะถูกเก็บใน DB ของ backend",
)


# =====================================================================
# MODE 1: DASHBOARD (ดึงข้อมูลจริงจาก maintenance_logs.db)
# =====================================================================
def render_dashboard(db_path: Path):
    st.markdown(
        "<h1 style='color:#007bff;'>🏭 Factory Machine Maintenance Dashboard</h1>",
        unsafe_allow_html=True,
    )

    df = load_logs_from_db(db_path)

    if df.empty:
        st.info(
            "ยังไม่มีข้อมูลในฐาน `logs/maintenance_logs.db` "
            "ลองให้ Maintenance Agent วิเคราะห์รูปอย่างน้อย 1 ครั้งก่อนนะครับ 🙂"
        )
        return
    
    # --------------------- แปลง + Filter พื้นฐาน ---------------------
    # เฉพาะ row ที่มี status (ถือว่าเป็นเหตุการณ์จริง)
    if "status" in df.columns:
        df = df[~df["status"].isna()].copy()

    # ฟิลเตอร์ Resolved / Unresolved จาก sidebar
    st.sidebar.markdown("---")
    resolved_filter = st.sidebar.selectbox(
        "Filter by issue status",
        options=["All", "Unresolved only", "Resolved only"],
        index=1,
    )

    df_filtered = df.copy()
    if resolved_filter == "Unresolved only":
        df_filtered = df_filtered[~df_filtered["resolved"]]
    elif resolved_filter == "Resolved only":
        df_filtered = df_filtered[df_filtered["resolved"]]

    # ใช้ df_filtered สำหรับกราฟ & ตารางด้านล่าง
        # --------------------- Overdue issues (>2 days, NG & ยังไม่แก้) ---------------------
    st.subheader("🔥 Unresolved NG issues older than 2 days")

    now = pd.Timestamp.now()  # ใช้ timezone เดียวกับ ts (naive)
    if "ts" in df.columns and "status" in df.columns:
        mask_overdue = (
            (df["status"] == "NG")
            & (~df["resolved"])
            & df["ts"].notna()
            & ((now - df["ts"]) > pd.Timedelta(days=2))
        )
        overdue = df[mask_overdue].copy()
    else:
        overdue = pd.DataFrame()

    if overdue.empty:
        st.success("ตอนนี้ไม่มีปัญหาค้างเกิน 2 วัน 🎉")
    else:
        cols_overdue = [
            c
            for c in ["ts", "client_id", "defect_type", "status", "resolved"]
            if c in overdue.columns
        ]
        st.dataframe(overdue[cols_overdue], use_container_width=True)

    # --------------------- KPI ---------------------
    total = len(df_filtered)

    if "status" in df_filtered.columns:
        ok_count = (df_filtered["status"] == "OK").sum()
        ng_count = (df_filtered["status"] == "NG").sum()
    else:
        ok_count = ng_count = 0

    if total > 0 and ok_count is not None:
        uptime = ok_count / total * 100.0
    else:
        uptime = None

    if "latency_ms" in df.columns and not df_filtered["latency_ms"].isna().all():
        avg_latency = df_filtered["latency_ms"].mean()
    else:
        avg_latency = None

    critical_defects = ng_count if ng_count is not None else None

    # เตรียมข้อความสำหรับแสดง
    if total > 0:
        uptime = ok_count / total * 100.0
        uptime_str = f"{uptime:.1f}%"
    else:
        uptime_str = "No data"

    if "latency_ms" in df.columns and not df_filtered["latency_ms"].isna().all():
        avg_latency = df_filtered["latency_ms"].mean()
        latency_str = f"{avg_latency:.0f} ms"
    else:
        latency_str = "N/A"

    critical_defects = ng_count if ng_count is not None else None
    critical_str = critical_defects if critical_defects is not None else "N/A"

    # ----- 3 KPI cards -----
    col1, col2, col3 = st.columns(3)

    # Uptime card (ให้ดันขึ้นมาเป็นกรอบเหมือนตัวอื่น)
    with col1:
        st.markdown(
            f"""
            <div style='padding:20px; background:white; border-radius:10px;
                        border-left:6px solid #28a745; box-shadow:0 2px 4px rgba(0,0,0,0.1);'>
                <h4>Uptime (%)</h4>
                <h1 style='color:#28a745;'>{uptime_str}</h1>
                <p>OK / (OK + NG) ภายใต้ filter ปัจจุบัน</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Avg latency card (เหมือนเดิม)
    with col2:
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

    # Critical defects card (เหมือนเดิม)
    with col3:
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

    # --------------------- Charts ---------------------
    left, right = st.columns(2)

    # Defect frequency (ใช้ df_filtered)
    if "defect_type" in df_filtered.columns:
        defect_counts = (
            df_filtered["defect_type"]
            .fillna("unknown")
            .value_counts()
            .rename_axis("Defect")
            .reset_index(name="Count")
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

    # Failure count per client (แทน Latency Trend เดิม)
    with right:
        st.subheader("🚨 Failure Count by Client")
        if "client_id" in df_filtered.columns and "status" in df_filtered.columns:
            df_fail = (
                df_filtered[df_filtered["status"] == "NG"]
                .groupby("client_id")
                .size()
                .reset_index(name="FailureCount")
                .sort_values("FailureCount", ascending=False)
            )
            if df_fail.empty:
                st.write("ยังไม่มีเครื่องที่มีสถานะ NG")
            else:
                fig2 = px.bar(
                    df_fail,
                    x="client_id",
                    y="FailureCount",
                    text="FailureCount",
                    template="simple_white",
                )
                fig2.update_traces(textposition="outside")
                st.plotly_chart(fig2, use_container_width=True)
        else:
            st.write("ยังไม่มีข้อมูล client_id หรือ status")


    # --------------------- Logs Table (editable resolved flag) ---------------------
    st.subheader("🛠 Recent Maintenance Logs")

    # ใช้ df_filtered แต่ต้องมี id / resolved ด้วย
    df_view = df_filtered.copy()
    if "id" in df_view.columns:
        df_view = df_view.set_index("id", drop=False)

    cols_show = []
    for c in ["id", "ts", "client_id", "defect_type", "status", "confidence", "latency_ms", "resolved"]:
        if c in df_view.columns:
            cols_show.append(c)

    if cols_show:
        edited = st.data_editor(
            df_view[cols_show].head(200),
            num_rows="fixed",
            use_container_width=True,
            column_config={
                "resolved": st.column_config.CheckboxColumn("Resolved"),
            },
            key="logs_editor",
        )

        if st.button("💾 Save resolved status"):
            update_resolved_flags(DB_PATH, edited)
            st.success("อัปเดตสถานะแก้ไขเรียบร้อยแล้ว (log ใหม่จะถูกใช้ในการรันครั้งถัดไป)")
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
    render_dashboard(db_path)  # 👈 ส่ง path ที่กรอกจาก sidebar เข้าไป
else:
    render_agent()
