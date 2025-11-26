# Architecture Diagrams

## Option 1: Separate Processes (Development)

```
┌─────────────────────────────────────────────────────────────┐
│                        Your Machine                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Terminal 1                          Terminal 2            │
│  ┌──────────────────┐                ┌──────────────────┐  │
│  │   FastAPI        │                │   Streamlit      │  │
│  │   Backend        │◄───────JSON────│   Frontend       │  │
│  │                  │────────Request──►                 │  │
│  │ port: 8000       │                │ port: 8501       │  │
│  │                  │                │                  │  │
│  │ - Vision Model   │                │ - Upload Image   │  │
│  │ - RAG Index      │                │ - Show Results   │  │
│  │ - SQLite Logs    │                │ - UI/UX          │  │
│  └──────────────────┘                └──────────────────┘  │
│         ▲                                    ▲              │
│         │ http://localhost:8000/docs        │              │
│         │                                   │              │
│         └───────────────────────────────────┘              │
│                  Browser (localhost)                        │
└─────────────────────────────────────────────────────────────┘
```

**How to run:**
```bash
# Terminal 1
python maintenance_agent_backend.py

# Terminal 2  
streamlit run app/maintenance_agent_frontend.py
```

---

## Option 2: Streamlit Auto-Launches Backend (RECOMMENDED)

```
┌─────────────────────────────────────────────────────────────┐
│                        Your Machine                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Single Command: streamlit run app_with_embedded_api.py    │
│                                                             │
│  ┌────────────────────────────────────────────────────┐   │
│  │            Streamlit Process (PID: 1234)           │   │
│  ├────────────────────────────────────────────────────┤   │
│  │                                                    │   │
│  │  ┌──────────────────────────────────────────┐    │   │
│  │  │  Streamlit Frontend (Main Thread)        │    │   │
│  │  │  port: 8501                              │    │   │
│  │  │                                          │    │   │
│  │  │  - File Upload                           │    │   │
│  │  │  - Display Results                       │    │   │
│  │  │  - User Interaction                      │    │   │
│  │  └───────────────────┬──────────────────────┘    │   │
│  │                      │                          │   │
│  │                      │ POST /analyze (JSON)     │   │
│  │                      ▼                          │   │
│  │  ┌──────────────────────────────────────────┐    │   │
│  │  │  FastAPI Backend (Subprocess)            │    │   │
│  │  │  port: 8001                              │    │   │
│  │  │                                          │    │   │
│  │  │  - Vision Model                          │    │   │
│  │  │  - RAG Index                             │    │   │
│  │  │  - SQLite Logs                           │    │   │
│  │  └──────────────────────────────────────────┘    │   │
│  │                                                    │   │
│  └────────────────────────────────────────────────────┘   │
│                                                             │
│  Browser: http://localhost:8501                            │
│  (Auto-starts FastAPI on 8001)                             │
└─────────────────────────────────────────────────────────────┘
```

**How to run:**
```bash
streamlit run app_with_embedded_api.py
# Opens http://localhost:8501 automatically
```

---

## Option 3: Unified Single-Process (Production)

```
┌─────────────────────────────────────────────────────────────┐
│                        Your Machine                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Single Command: streamlit run unified_app.py              │
│                                                             │
│  ┌────────────────────────────────────────────────────┐   │
│  │        Unified Python Process (PID: 1234)          │   │
│  ├────────────────────────────────────────────────────┤   │
│  │                                                    │   │
│  │  Main Thread: Streamlit UI                        │   │
│  │  ├─ File Upload Handling                          │   │
│  │  ├─ Display Results                               │   │
│  │  └─ User Input                                    │   │
│  │         │                                          │   │
│  │         │ Direct function call (no HTTP)          │   │
│  │         ▼                                          │   │
│  │  Background Thread: FastAPI Processing            │   │
│  │  ├─ Vision Model (call_vlm_stub)                  │   │
│  │  ├─ RAG Index Search (manual_index)               │   │
│  │  ├─ SQLite Logging (save_log)                     │   │
│  │  └─ Return response dict                          │   │
│  │         │                                          │   │
│  │         └─ Back to Streamlit (instant)            │   │
│  │                                                    │   │
│  │  Both listening on:                               │   │
│  │  - Streamlit: port 8501                           │   │
│  │  - FastAPI: no external port (internal only)      │   │
│  │                                                    │   │
│  └────────────────────────────────────────────────────┘   │
│                                                             │
│  Browser: http://localhost:8501                            │
│  (All processing happens in one process)                   │
└─────────────────────────────────────────────────────────────┘
```

**How to run:**
```bash
streamlit run unified_app.py
# Opens http://localhost:8501 automatically
```

---

## Data Flow Across All Options

```
┌──────────────────────────────────────────────────────────────┐
│                     User Action                              │
│               Upload Machine Image                           │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
         ┌──────────────────────────┐
         │   Base64 Encode Image    │
         │   + Optional Question    │
         │   + Client ID            │
         └────────────┬─────────────┘
                      │
                      ▼
         ┌──────────────────────────────┐
         │   POST /analyze JSON         │
         │   {image_base64, question}   │
         └────────────┬─────────────────┘
                      │
      ┌───────────────┼───────────────┐
      │               │               │
   Option 1        Option 2        Option 3
   HTTP Call      HTTP Call    In-Process Call
      │               │               │
      ▼               ▼               ▼
   ┌──────────────────────────────────────┐
   │      1. Decode Image (PIL)           │
   │      2. Call Vision Stub             │
   │         → defect_type, status, conf  │
   │      3. RAG Search                   │
   │         → query = defect_type        │
   │         → find top-k manuals         │
   │      4. Generate Action Text         │
   │         (based on status + sources)  │
   │      5. Save Log                     │
   │         → SQLite DB                  │
   │         → Image file (PNG)           │
   └──────────────────┬───────────────────┘
                      │
                      ▼
      ┌───────────────────────────────────┐
      │   AnalyzeResponse JSON            │
      │   {                               │
      │     status: "OK" | "NG"           │
      │     defect_type: str              │
      │     confidence: float             │
      │     action_recommended: str       │
      │     rag_sources: [...]            │
      │     latency_ms: float             │
      │   }                               │
      └──────────────┬────────────────────┘
                     │
   ┌──────────────┬──┴──┬──────────────┐
   │ Option 1     │ Option 2     │ Option 3
   │ HTTP Resp    │ HTTP Resp    │ Dict Returned
   │              │              │
   ▼              ▼              ▼
┌────────────────────────────────────────┐
│      Display Results in Streamlit      │
│      - Status badge (OK/ALERT)         │
│      - Confidence percentage           │
│      - Defect type with icon           │
│      - Recommended actions (rich text) │
│      - Reference manuals (expandable)  │
└────────────────────────────────────────┘
```

---

## Deployment Path Flowchart

```
┌──────────────┐
│  Start Here  │
└──────┬───────┘
       │
       ▼
   What's your
    use case?
       │
   ┌───┼───┬──────────┐
   │   │   │          │
   ▼   ▼   ▼          ▼
Local Dev  Cloud  Docker   Production
   │       │        │          │
   ▼       ▼        ▼          ▼
Option1 Option3 Option3    Option3+
or      (best    (best    (separate
Option2 choice) choice)   backend
(easiest)                  + LB)
   │       │        │          │
   └───┬───┴────┬───┴──────────┘
       │        │
       ▼        ▼
   Works?  Works?
    YES     YES
     │       │
     ▼       ▼
   Done! Configure:
   Add:   - Auth
   - VLM  - DB backup
   - PDFs - Scaling
   - Test - Monitoring
```

---

## File Organization After Setup

```
maintenance-agent/
│
├── maintenance_agent_backend.py      ← FastAPI app (core logic)
├── app/
│   └── maintenance_agent_frontend.py ← Original Streamlit (Option 1)
│
├── app_with_embedded_api.py          ← NEW: Subprocess integration (Option 2)
├── unified_app.py                    ← NEW: All-in-one (Option 3)
│
├── manuals/                          ← PDFs for RAG
│   ├── pump_manual.pdf
│   ├── hydraulic_system.pdf
│   └── ...
│
├── logs/                             ← Auto-created
│   ├── maintenance_logs.db           ← SQLite database
│   ├── 2025-11-26T10-30-45...OK.png  ← Logged images
│   └── ...
│
├── manual_index.npz                  ← Cached embeddings
│
├── requirements.txt                  ← Python dependencies
├── .github/
│   └── copilot-instructions.md       ← AI agent guide
│
├── DEPLOYMENT.md                     ← Detailed deployment guide
├── QUICKSTART.md                     ← Quick reference
└── SETUP_COMPLETE.md                 ← This setup summary
```

---

## Which Option to Choose?

```
┌─────────────────────────────────────────────────────────┐
│ I want to...                      │ Use Option │ Command │
├───────────────────────────────────┼────────────┼─────────┤
│ Start right now (simplest)        │     2     │streamlit│
│ Debug backend + frontend separate │     1     │2 terms  │
│ Deploy to Streamlit Cloud         │     3     │streamlit│
│ Docker / Heroku / Production      │     3     │docker   │
│ Integrate real VLM API            │   1 or 3  │varies   │
│ Scale to many users               │   1 (sep) │complex  │
└─────────────────────────────────────────────────────────┘
```

---

**TL;DR**: 
- **Quick start**: `streamlit run app_with_embedded_api.py` (Option 2)
- **Development**: Use Option 1 (2 terminals)
- **Production**: Use Option 3 (unified_app.py)
