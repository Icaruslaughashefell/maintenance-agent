"""
maintenance_agent_frontend.py
=============================================
Streamlit UI สำหรับ Maintenance Agent (Multi-client)

- Upload รูป
- พิมพ์คำถามเสริม (optional)
- ระบุ client_id (เช่น ชื่อเครื่อง / operator)
- ส่งไป backend /analyze
- แสดงผลแบบอ่านง่าย
"""

import base64
import time

import requests
import streamlit as st

DEFAULT_API_URL = "http://127.0.0.1:8000/analyze"

st.set_page_config(page_title="Maintenance Agent Demo", layout="wide")
st.title("🛠️ Maintenance Agent – Vision + RAG Demo")


# ------------------------------------------------------------
# Sidebar config
# ------------------------------------------------------------
st.sidebar.header("Settings")
api_url = st.sidebar.text_input("Backend API URL", DEFAULT_API_URL)
client_id = st.sidebar.text_input(
    "Client ID (ชื่อเครื่อง/ผู้ใช้งาน)",
    value="client-1",
    help="ใช้สำหรับระบุว่า log นี้มาจากเครื่องไหน จะถูกเก็บใน DB ของ backend",
)


# ------------------------------------------------------------
# Main layout
# ------------------------------------------------------------
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("1) Upload Machine Image")
    uploaded_file = st.file_uploader("Choose an image", type=["jpg", "jpeg", "png"])

    user_question = st.text_area(
        "Optional question (e.g. specific symptom / sound / vibration)",
        help="ข้อความนี้จะถูกส่งไปเสริม prompt ให้ VLM",
    )

    file_bytes = None
    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        st.image(file_bytes, caption="Preview", use_column_width=True)

    run_button = st.button("Analyze", type="primary")

with col_right:
    st.subheader("2) Result")

    if run_button:
        if file_bytes is None:
            st.warning("กรุณาอัปโหลดรูปก่อน")
        else:
            img_b64 = base64.b64encode(file_bytes).decode("utf-8")

            payload = {
                "image_base64": img_b64,
                "question": user_question or None,
                "client_id": client_id or None,
            }

            try:
                with st.spinner("Analyzing..."):
                    t0 = time.time()
                    resp = requests.post(api_url, json=payload, timeout=60)
                    roundtrip_ms = (time.time() - t0) * 1000

                if resp.status_code != 200:
                    st.error(f"API error: {resp.status_code} {resp.text}")
                else:
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