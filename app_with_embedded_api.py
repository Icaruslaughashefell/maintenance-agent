"""
app_with_embedded_api.py
=====================================================
Single-file Streamlit app with:
- Embedded FastAPI backend (auto-starts on port 8001)
- Modernized UI (Vision + RAG results)
- Upload image + optional question + client_id
- Clean result display with metrics + expanders

Run with:
    streamlit run app_with_embedded_api.py
"""

import base64
import time
import subprocess
import os
import sys
import requests
import streamlit as st

# ------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------
FASTAPI_PORT = 8001
API_BASE_URL = f"http://127.0.0.1:{FASTAPI_PORT}"

BACKEND_FILE = "maintenance_agent_backend.py"

st.set_page_config(
    page_title="Maintenance Agent",
    page_icon="🛠️",
    layout="wide",
)


# ------------------------------------------------------------
# BACKEND AUTO-STARTER
# ------------------------------------------------------------
def ensure_backend_running():
    """Checks backend, starts subprocess if needed."""
    try:
        requests.get(f"{API_BASE_URL}/docs", timeout=1)
        return True
    except:
        st.warning("🔄 Starting FastAPI backend in the background...")

        subprocess.Popen(
            [sys.executable, BACKEND_FILE],
            env={**os.environ, "FASTAPI_PORT": str(FASTAPI_PORT)},
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        time.sleep(3)
        return False


ensure_backend_running()


# ------------------------------------------------------------
# HEADER
# ------------------------------------------------------------
st.title("🛠️ Maintenance Agent – Vision + RAG Demo")
st.caption("อัปโหลดรูป → ตรวจจับ defect → ดึงคำแนะนำจากคู่มืออัตโนมัติ")


# ------------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------------
st.sidebar.header("⚙️ Settings")

client_id = st.sidebar.text_input(
    "Client ID",
    value="client-1",
    help="ระบุชื่อเครื่องหรือผู้ใช้งาน"
)


# ------------------------------------------------------------
# TWO-COLUMN LAYOUT
# ------------------------------------------------------------
col_left, col_right = st.columns([1, 1])

# ------------------------------------------------------------
# LEFT COLUMN — Upload
# ------------------------------------------------------------
with col_left:
    st.subheader("📤 Step 1 — Upload Machine Image")

    uploaded_file = st.file_uploader(
        "Choose an image",
        type=["jpg", "jpeg", "png"],
    )

    user_question = st.text_area(
        "Optional question",
        placeholder="เสียงดังผิดปกติ / สั่น / ร้อนมาก / ฯลฯ",
        help="ข้อความนี้จะถูกเพิ่มไปใน prompt",
    )

    file_bytes = None
    if uploaded_file:
        file_bytes = uploaded_file.getvalue()
        st.image(file_bytes, caption="Preview", use_column_width=True)

    run_button = st.button("🚀 Analyze", type="primary")


# ------------------------------------------------------------
# RIGHT COLUMN — Results
# ------------------------------------------------------------
with col_right:
    st.subheader("📊 Step 2 — Analysis Result")

    if run_button:

        if not file_bytes:
            st.warning("⚠️ กรุณาอัปโหลดรูปก่อนค่ะ")
        else:
            img_b64 = base64.b64encode(file_bytes).decode()

            payload = {
                "image_base64": img_b64,
                "question": user_question or None,
                "client_id": client_id,
            }

            try:
                with st.spinner("🔍 Analyzing..."):
                    t0 = time.time()
                    resp = requests.post(
                        f"{API_BASE_URL}/analyze",
                        json=payload,
                        timeout=120
                    )
                    roundtrip_ms = (time.time() - t0) * 1000

                if resp.status_code != 200:
                    st.error(f"❌ API Error {resp.status_code}:\n{resp.text}")
                else:
                    data = resp.json()

                    # ------------------------
                    # METRIC GRID
                    # ------------------------
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Status", data["status"])
                    m2.metric("Defect Type", data["defect_type"])
                    m3.metric("Confidence", f"{data['confidence']:.2%}")
                    m4.metric("Latency", f"{data.get('latency_ms', 0):.0f}ms")

                    st.markdown("---")

                    # ------------------------
                    # ACTION RECOMMENDED
                    # ------------------------
                    st.markdown("### 🔧 Recommended Action")
                    st.success(data["action_recommended"])

                    st.markdown("---")

                    # ------------------------
                    # RAG SOURCES
                    # ------------------------
                    st.markdown("### 📚 Reference Materials")

                    if data["rag_sources"]:
                        for i, src in enumerate(data["rag_sources"], 1):
                            with st.expander(
                                f"Source {i}: {src['manual_name']} (p.{src['page']}) — score={src['score']:.2f}"
                            ):
                                st.write(src["snippet"])
                    else:
                        st.info("No manual references found for this defect type.")

                    st.markdown("---")

                    # ------------------------
                    # RAW JSON
                    # ------------------------
                    st.markdown("### 🐍 Raw JSON")
                    st.json(data)

            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot reach backend on port 8001")
            except Exception as e:
                st.error(f"❌ Error: {e}")


# ------------------------------------------------------------
# FOOTER
# ------------------------------------------------------------
st.divider()
st.markdown(
    """
**Maintenance Agent System**  
FastAPI backend (auto-started) · Streamlit frontend  
Vision + RAG · Industrial Diagnostics  
"""
)
