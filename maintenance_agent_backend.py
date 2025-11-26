"""
maintenance_agent_backend.py
====================================================
Backend สำหรับ Maintenance Agent (Multi-client, Central DB)

- FastAPI + Uvicorn
- Vision Stub + RAG จาก PDF
- Log ทุก request ลง SQLite + เซฟรูปในโฟลเดอร์ logs/ บนเครื่องเซิร์ฟเวอร์
"""

import base64
import io
import time
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from sklearn.neighbors import NearestNeighbors
from pypdf import PdfReader
from PIL import Image

# ------------------------------------------------------------
# ========== Config Paths ====================================
# ------------------------------------------------------------

ROOT_DIR = Path(__file__).parent
MANUAL_DIR = ROOT_DIR / "manuals"          # PDF manuals
INDEX_PATH = ROOT_DIR / "manual_index.npz" # RAG index
LOG_DIR = ROOT_DIR / "logs"                # images + db
DB_PATH = LOG_DIR / "maintenance_logs.db"  # SQLite DB

CHUNK_SIZE = 800
CHUNK_OVERLAP = 200


# ------------------------------------------------------------
# ========== API Schemas =====================================
# ------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    image_base64: str
    question: Optional[str] = None
    client_id: Optional[str] = None   # ระบุชื่อเครื่อง / user ก็ได้


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


# ------------------------------------------------------------
# ========== RAG Index =======================================
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# ========== Vision Stub =====================================
# ------------------------------------------------------------

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
...
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


# ------------------------------------------------------------
# ========== Logging (SQLite + images) =======================
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# ========== FastAPI App =====================================
# ------------------------------------------------------------

app = FastAPI(title="Maintenance Agent Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ใน production ควรจำกัด origin
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

    # 1) decode รูป
    img, img_bytes = decode_image(req.image_base64)

    # 2) คอล Vision (ตอนนี้ใช้ stub)
    _ = build_vision_prompt(req.question)  # เผื่อใช้ในอนาคตกับ VLM จริง
    vision_result = call_vlm_stub(req.image_base64, req.question)

    defect_type = vision_result["defect_type"]
    status = vision_result["status"]
    confidence = float(vision_result["confidence"])

    # 3) RAG
    rag_query = defect_type if defect_type != "normal" else "preventive maintenance"
    rag_results = manual_index.search(rag_query, top_k=3)

    # 4) สร้างข้อความแนะนำ
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

    # 5) เซฟ log บนเครื่องเซิร์ฟเวอร์
    save_log(req, resp_obj, img_bytes)

    return resp_obj


if __name__ == "__main__":
    import uvicorn
    import os

    # Get port from environment or use default
    port = int(os.getenv("FASTAPI_PORT", "8000"))

    # host=0.0.0.0 เพื่อให้เครื่องอื่นใน LAN เรียกได้
    uvicorn.run(
        "maintenance_agent_backend:app",
        host="0.0.0.0",
        port=port,
        reload=True,
    )