"""
unified_app.py
=====================================================
Unified Streamlit + FastAPI Deployment
- Runs FastAPI as background thread
- Streamlit frontend calls local FastAPI server
- Single deployment; both accessible on default Streamlit port
"""

import base64
import io
import time
import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

import numpy as np
import streamlit as st
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from sklearn.neighbors import NearestNeighbors
from pypdf import PdfReader
from PIL import Image
import uvicorn

# ============================================================
# ========== CONFIG & PATHS ================================
# ============================================================

ROOT_DIR = Path(__file__).parent
MANUAL_DIR = ROOT_DIR / "manuals"
INDEX_PATH = ROOT_DIR / "manual_index.npz"
LOG_DIR = ROOT_DIR / "logs"
DB_PATH = LOG_DIR / "maintenance_logs.db"

CHUNK_SIZE = 800
CHUNK_OVERLAP = 200
FASTAPI_PORT = 8001  # Changed from 8000 to avoid conflicts
API_BASE_URL = f"http://127.0.0.1:{FASTAPI_PORT}"

# ============================================================
# ========== FASTAPI SCHEMAS ===============================
# ============================================================

class AnalyzeRequest(BaseModel):
    image_base64: str
    question: Optional[str] = None
    client_id: Optional[str] = None


class RAGSource(BaseModel):
    manual_name: str
    page: int
    score: float
    snippet: str


class AnalyzeResponse(BaseModel):
    status: str
    defect_type: str
    confidence: float
    action_recommended: str
    rag_sources: List[RAGSource]
    latency_ms: float


# ============================================================
# ========== RAG INDEX CLASS ===============================
# ============================================================

class ManualIndex:
    def __init__(self):
        self.texts: List[str] = []
        self.meta: List[Dict[str, Any]] = []
        self.model: Optional[SentenceTransformer] = None
        self.nn: Optional[NearestNeighbors] = None
        self.embeddings: Optional[np.ndarray] = None

    def build_from_pdfs(self, pdf_dir: Path):
        print(f"[RAG] Building index from PDFs in {pdf_dir} ...")
        self.texts = []
        self.meta = []

        for pdf_path in pdf_dir.glob("*.pdf"):
            reader = PdfReader(str(pdf_path))
            for page_idx, page in enumerate(reader.pages):
                raw_text = page.extract_text() or ""
                raw_text = raw_text.strip()
                if not raw_text:
                    continue
                chunks = self._split_into_chunks(raw_text)
                for chunk in chunks:
                    self.texts.append(chunk)
                    self.meta.append({
                        "manual_name": pdf_path.name,
                        "page": page_idx + 1,
                    })

        if not self.texts:
            print("[RAG] WARNING: No text extracted from manuals.")
            return

        print("[RAG] Loading embedding model (sentence-transformers)...")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        print(f"[RAG] Encoding {len(self.texts)} chunks ...")
        self.embeddings = self.model.encode(self.texts, show_progress_bar=True)

        self.nn = NearestNeighbors(
            n_neighbors=5,
            metric="cosine"
        )
        self.nn.fit(self.embeddings)

        np.savez_compressed(
            INDEX_PATH,
            embeddings=self.embeddings,
            meta=np.array(self.meta, dtype=object),
            texts=np.array(self.texts, dtype=object),
        )
        print(f"[RAG] Index saved to {INDEX_PATH}")

    def load_or_build(self, pdf_dir: Path):
        if INDEX_PATH.exists():
            print(f"[RAG] Loading existing index from {INDEX_PATH}")
            data = np.load(INDEX_PATH, allow_pickle=True)
            self.embeddings = data["embeddings"]
            self.meta = list(data["meta"])
            self.texts = list(data["texts"])
            self.model = SentenceTransformer("all-MiniLM-L6-v2")
            self.nn = NearestNeighbors(n_neighbors=5, metric="cosine")
            self.nn.fit(self.embeddings)
        else:
            self.build_from_pdfs(pdf_dir)

    def _split_into_chunks(self, text: str) -> List[str]:
        text = " ".join(text.split())
        chunks = []
        start = 0
        while start < len(text):
            end = start + CHUNK_SIZE
            chunk = text[start:end]
            chunks.append(chunk)
            start += CHUNK_SIZE - CHUNK_OVERLAP
        return chunks

    def search(self, query: str, top_k: int = 3) -> List[RAGSource]:
        if not self.model or not self.nn or self.embeddings is None:
            return []
        q_emb = self.model.encode([query])
        distances, indices = self.nn.kneighbors(q_emb, n_neighbors=top_k)
        results: List[RAGSource] = []
        for dist, idx in zip(distances[0], indices[0]):
            meta = self.meta[idx]
            snippet = self.texts[idx]
            results.append(RAGSource(
                manual_name=meta["manual_name"],
                page=meta["page"],
                score=float(1 - dist),
                snippet=snippet[:400],
            ))
        return results


manual_index = ManualIndex()


# ============================================================
# ========== VISION STUB ===================================
# ============================================================

def decode_image(image_base64: str) -> Tuple[Image.Image, bytes]:
    try:
        img_bytes = base64.b64decode(image_base64)
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        return img, img_bytes
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image base64: {e}")


def build_vision_prompt(question: Optional[str] = None) -> str:
    base = """
You are an expert maintenance engineer in a factory.
You receive a photo of a machine/component.
Analyze it and detect any defects: rust, leaks, cracks, loose bolts, misalignment, etc.
Respond ONLY in JSON format with: {"defect_type": "...", "status": "OK" or "NG", "confidence": 0.0-1.0}
"""
    if question:
        base += f"\nUser additional question: {question}\n"
    base += "\nNow analyze the image and output ONLY the JSON.\n"
    return base


def call_vlm_stub(image_base64: str, question: Optional[str] = None) -> Dict[str, Any]:
    import random
    defect_candidates = ["normal", "rust_on_pipe", "oil_leak", "loose_bolt"]
    defect = random.choice(defect_candidates)
    if defect == "normal":
        status = "OK"
        conf = 0.9
    else:
        status = "NG"
        conf = random.uniform(0.7, 0.95)

    return {
        "defect_type": defect,
        "status": status,
        "confidence": conf,
        "note": "dummy VLM stub – please replace with real model call",
    }


# ============================================================
# ========== DATABASE LOGGING ==============================
# ============================================================

def init_db():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT,
            client_id TEXT,
            question TEXT,
            defect_type TEXT,
            status TEXT,
            confidence REAL,
            latency_ms REAL,
            image_path TEXT,
            response_json TEXT
        )
        """
    )
    conn.commit()
    conn.close()
    print(f"[DB] SQLite ready at {DB_PATH}")


def save_log(req: AnalyzeRequest, resp: AnalyzeResponse, img_bytes: bytes) -> None:
    ts = datetime.utcnow().isoformat()
    safe_ts = ts.replace(":", "-")
    client_id = req.client_id or "unknown"

    # เซฟรูป
    filename = f"{safe_ts}_{resp.defect_type}_{resp.status}.png"
    img_path = LOG_DIR / filename
    with open(img_path, "wb") as f_img:
        f_img.write(img_bytes)

    # เซฟ log ใน DB
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO logs (
            ts, client_id, question, defect_type, status,
            confidence, latency_ms, image_path, response_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ts,
            client_id,
            req.question,
            resp.defect_type,
            resp.status,
            resp.confidence,
            resp.latency_ms,
            str(img_path),
            resp.model_dump_json(ensure_ascii=False),
        ),
    )
    conn.commit()
    conn.close()


# ============================================================
# ========== FASTAPI APP ==================================
# ============================================================

app = FastAPI(title="Maintenance Agent Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    MANUAL_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    init_db()
    manual_index.load_or_build(MANUAL_DIR)
    print("[Startup] RAG index ready.")


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    t0 = time.time()

    # 1) Decode image
    img, img_bytes = decode_image(req.image_base64)

    # 2) Call Vision (stub)
    _ = build_vision_prompt(req.question)
    vision_result = call_vlm_stub(req.image_base64, req.question)

    defect_type = vision_result["defect_type"]
    status = vision_result["status"]
    confidence = float(vision_result["confidence"])

    # 3) RAG retrieval
    rag_query = defect_type if defect_type != "normal" else "preventive maintenance"
    rag_results = manual_index.search(rag_query, top_k=3)

    # 4) Generate action text
    if not rag_results:
        if status == "OK":
            action_text = (
                "No obvious defect detected. Continue normal operation but monitor periodically."
            )
        else:
            action_text = (
                "A defect is detected, but no matching manual section was found. "
                "Please check the machine manually and consult senior engineer."
            )
    else:
        top_snippets = "\n\n---\n\n".join(
            f"[{src.manual_name} p.{src.page}] {src.snippet}"
            for src in rag_results
        )
        if status == "OK":
            action_text = (
                f"Status appears OK (defect_type={defect_type}).\n\n"
                f"Relevant preventive maintenance info:\n{top_snippets}"
            )
        else:
            action_text = (
                f"Detected defect='{defect_type}' with confidence={confidence:.2f}.\n\n"
                f"Recommended actions from manuals:\n{top_snippets}"
            )

    latency_ms = (time.time() - t0) * 1000

    resp_obj = AnalyzeResponse(
        status=status,
        defect_type=defect_type,
        confidence=confidence,
        action_recommended=action_text,
        rag_sources=rag_results,
        latency_ms=latency_ms,
    )

    # 5) Save log
    save_log(req, resp_obj, img_bytes)

    return resp_obj


# ============================================================
# ========== STREAMLIT FRONTEND ============================
# ============================================================

def run_fastapi_in_thread():
    """Run FastAPI server in a background thread"""
    config = uvicorn.Config(
        app=app,
        host="127.0.0.1",
        port=FASTAPI_PORT,
        log_level="info"
    )
    server = uvicorn.Server(config)
    asyncio.run(server.serve())


# Initialize FastAPI server once when Streamlit starts
if "fastapi_started" not in st.session_state:
    import asyncio
    
    # Start FastAPI in background thread
    fastapi_thread = threading.Thread(target=run_fastapi_in_thread, daemon=True)
    fastapi_thread.start()
    
    # Give server time to start
    time.sleep(2)
    
    st.session_state.fastapi_started = True


# Streamlit UI
st.set_page_config(page_title="Maintenance Agent", layout="wide")
st.title("🛠️ Maintenance Agent – Vision + RAG")

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
                st.error("❌ Cannot connect to backend. Is FastAPI running?")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")


# Footer
st.divider()
st.markdown("""
---
**Maintenance Agent** | Vision + RAG System for Factory Diagnostics
- Backend: FastAPI running internally
- Frontend: Streamlit
""")
