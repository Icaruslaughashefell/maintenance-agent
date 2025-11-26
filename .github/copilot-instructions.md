# Copilot Instructions: Maintenance Agent

## Project Overview

**Maintenance Agent** is a multi-component AI system for factory machine diagnostics combining computer vision (VLM), retrieval-augmented generation (RAG), and structured logging. Architecture:

- **Backend** (`maintenance_agent_backend.py`): FastAPI server (port 8000) handling image analysis, RAG retrieval, and database logging
- **Frontend** (`app/maintenance_agent_frontend.py`): Streamlit UI (port 8501) for image upload and result visualization
- **Vision Module** (`vision/vision.py`): VLM integration stub (currently random; needs real model replacement)
- **RAG Module** (`rag/rag.py`): Placeholder; core RAG logic is embedded in backend
- **Data Flow**: Image (base64) → Vision analysis → RAG retrieval from PDF manuals → JSON response with action recommendations

## Critical Architecture Patterns

### 1. **API Contract: Always Return Structured JSON**
The backend's `/analyze` endpoint returns `AnalyzeResponse` (see lines 45–51 of backend). All responses MUST include:
```python
{
  "status": "OK" | "NG",
  "defect_type": str,
  "confidence": float,
  "action_recommended": str,
  "rag_sources": List[RAGSource],
  "latency_ms": float
}
```
When extending vision or RAG modules, ensure outputs conform to this schema. The frontend expects this exact structure (see `app/maintenance_agent_frontend.py` lines 77–87).

### 2. **RAG Index Built on Startup**
The `ManualIndex` class (lines 63–135 of backend) loads or builds embeddings at startup via `manual_index.load_or_build()` (line 336). Key behaviors:
- PDFs go in `manuals/` folder
- Chunks: 800 chars with 200 overlap (lines 32–33)
- Uses `sentence-transformers/all-MiniLM-L6-v2` for embeddings
- Saves compressed index to `manual_index.npz`
- Searches via cosine distance with top-k=5 neighbors
When adding new PDFs, the index rebuilds automatically on next startup. Chunk size/overlap are tunable but affect embedding speed and memory.

### 3. **Multi-Client Logging: SQLite + Image Storage**
Every request is logged in `logs/maintenance_logs.db` with image saved as PNG (see `save_log()`, lines 229–260). Fields:
- `client_id`: Machine/operator identifier (optional; defaults to "unknown")
- Image filename: `{timestamp}_{defect_type}_{status}.png`
- Full response JSON stored for replay

This enables multi-machine tracking and audit trails. Keep `LOG_DIR` writable by the uvicorn process.

### 4. **Vision Module Is a Stub Awaiting Real Implementation**
Current `call_vlm_stub()` (lines 187–201) returns random defects. To integrate a real VLM (GPT-4o, Gemini, Claude Vision):
1. Replace stub with actual API call
2. Parse vision output into `{"defect_type": str, "status": str, "confidence": float, ...}`
3. Ensure response latency is captured
4. Handle rate limits and API failures gracefully (return HTTP 503 or NG status)

The prompt template is in `build_vision_prompt()` (lines 173–184); extend it for domain-specific instructions.

### 5. **RAG Fallback Behavior**
If no RAG sources match (empty results), the backend still returns an `AnalyzeResponse` with action text based on status:
- **Status OK + no sources**: Recommend preventive maintenance
- **Status NG + no sources**: Recommend manual inspection + senior engineer
This ensures the API never returns incomplete responses even with poor PDF coverage.

## Development Workflows

### Setup & Running Locally
```bash
# Install dependencies
pip install -r requirements.txt

# Backend (terminal 1)
cd /Users/theeramet/MasterDegree/maintenance-agent
python maintenance_agent_backend.py
# Starts at http://localhost:8000; /docs for Swagger UI

# Frontend (terminal 2)
streamlit run app/maintenance_agent_frontend.py
# Opens at http://localhost:8501
```

### Testing the API
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"image_base64":"<base64>","client_id":"test-machine"}'
```

### Adding Manual PDFs
1. Place PDFs in `manuals/` folder (e.g., `manuals/pump_manual.pdf`)
2. Delete `manual_index.npz` to force rebuild
3. Restart backend; embeddings rebuild on startup

## Code Style & Project Conventions

- **Language Mix**: Backend/RAG in Python; some Thai comments (e.g., "เซฟรูป") for clarity among Thai-speaking team
- **Error Handling**: Use FastAPI's `HTTPException` with descriptive messages; avoid silent failures
- **Paths**: Use `pathlib.Path` (see `ROOT_DIR`, `MANUAL_DIR`, etc.) for cross-platform compatibility
- **Logging**: Print to console for startup info; database logs for request audit trail
- **CORS**: Currently allows `"*"` (see line 315); restrict in production to specific frontend origin

## Common Modifications

### Extend Defect Type Classification
Modify the stub or real VLM call to return new defect types. Update test images and RAG chunk tagging if needed. The frontend will display any string in the response without change.

### Adjust RAG Sensitivity
- Increase `top_k` in `manual_index.search()` (default 3) for more sources
- Lower `CHUNK_SIZE` (line 33) for finer-grained relevance but higher latency
- Change embedding model in `ManualIndex.load_or_build()` (line 114) for different semantic quality

### Add Custom Request Fields
Extend `AnalyzeRequest` (lines 37–41) with new fields (e.g., `machine_type`, `ambient_temp`). Update the frontend form and backend logic to use them.

## Known Limitations & TODOs

- Vision module is a random stub; integrating real VLM is **blocking priority**
- RAG module placeholder in `vision/rag.py` and `rag/rag.py`; core logic is in backend
- No authentication; add JWT or API key before multi-tenant production deployment
- Streamlit frontend has no error recovery; add retry logic for backend connection timeouts

## When Modifying This Guide

Update this file when:
- Adding new API endpoints or request/response fields
- Changing RAG indexing logic (chunk size, embedding model, vector database)
- Introducing external service integrations (VLM API, alternative embedding services)
- Documenting new developer workflows or testing procedures
