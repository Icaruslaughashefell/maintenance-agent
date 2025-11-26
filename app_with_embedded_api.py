"""
app_with_embedded_api.py
=====================================================
Simplified Streamlit App with Embedded FastAPI
Runs FastAPI in subprocess, Streamlit calls it locally
Single entry point: streamlit run app_with_embedded_api.py
"""

import base64
import time
import subprocess
import os
import sys
import requests
import streamlit as st

# Port configuration
FASTAPI_PORT = 8001
API_BASE_URL = f"http://127.0.0.1:{FASTAPI_PORT}"

# Start FastAPI backend as subprocess on first run
def ensure_backend_running():
    """Start the original backend.py as subprocess if not running"""
    try:
        # Quick health check
        resp = requests.get(f"{API_BASE_URL}/docs", timeout=2)
        return True
    except:
        # Backend not running, start it
        st.warning("🔄 Starting FastAPI backend in background...")
        
        # Modify port in backend before running
        backend_path = "maintenance_agent_backend.py"
        
        # Start subprocess
        subprocess.Popen(
            [sys.executable, backend_path],
            env={**os.environ, "FASTAPI_PORT": str(FASTAPI_PORT)},
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        # Wait for startup
        time.sleep(3)
        return False


# Streamlit UI
st.set_page_config(page_title="Maintenance Agent", layout="wide")
st.title("🛠️ Maintenance Agent – Vision + RAG")

# Ensure backend is running
ensure_backend_running()

# Sidebar config
st.sidebar.header("⚙️ Settings")
client_id = st.sidebar.text_input(
    "Client ID (Machine/User Name)",
    value="client-1",
    help="Identifier for this machine/operator"
)

# Main layout
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("1️⃣ Upload Machine Image")
    uploaded_file = st.file_uploader("Choose an image", type=["jpg", "jpeg", "png"])

    user_question = st.text_area(
        "Optional question (symptom/sound/vibration)",
        help="Additional context for the AI analysis"
    )

    file_bytes = None
    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        st.image(file_bytes, caption="Preview", use_column_width=True)

    run_button = st.button("🔍 Analyze", type="primary")

with col_right:
    st.subheader("2️⃣ Analysis Result")

    if run_button:
        if file_bytes is None:
            st.warning("⚠️ Please upload an image first")
        else:
            img_b64 = base64.b64encode(file_bytes).decode("utf-8")

            payload = {
                "image_base64": img_b64,
                "question": user_question or None,
                "client_id": client_id or None,
            }

            try:
                with st.spinner("🔄 Analyzing machine image..."):
                    t0 = time.time()
                    resp = requests.post(f"{API_BASE_URL}/analyze", json=payload, timeout=60)
                    roundtrip_ms = (time.time() - t0) * 1000

                if resp.status_code != 200:
                    st.error(f"❌ API Error: {resp.status_code}\n{resp.text}")
                else:
                    data = resp.json()

                    # Display key metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Status", data["status"], delta="OK" if data["status"] == "OK" else "ALERT")
                    with col2:
                        st.metric("Defect Type", data["defect_type"])
                    with col3:
                        st.metric("Confidence", f"{data['confidence']:.2%}")
                    with col4:
                        st.metric("Latency", f"{data.get('latency_ms', 0):.0f}ms")

                    # Action recommended
                    st.markdown("### 📋 Recommended Action")
                    st.write(data["action_recommended"])

                    # RAG sources
                    st.markdown("### 📚 Reference Materials")
                    if data["rag_sources"]:
                        for i, src in enumerate(data["rag_sources"], 1):
                            with st.expander(f"Source {i}: {src['manual_name']} (p.{src['page']}) — Score: {src['score']:.2f}"):
                                st.write(src["snippet"])
                    else:
                        st.info("No manual references found for this defect type.")

            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to backend. Check if FastAPI is running on port 8001")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")


# Footer
st.divider()
st.markdown("""
---
**Maintenance Agent** | Vision + RAG System for Factory Diagnostics
- Backend: FastAPI (port 8001)
- Frontend: Streamlit (this app)
""")
