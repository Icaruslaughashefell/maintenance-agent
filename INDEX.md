# 📋 Complete File Index & Documentation Guide

## 🎯 Where to Start

### 👉 **First Time?**
1. Read: **`START_HERE.md`** ← You are here
2. Run: `streamlit run app_with_embedded_api.py`
3. Open: `http://localhost:8501`

### 🔧 **Need to Understand Options?**
Read: **`ARCHITECTURE.md`** (visual diagrams of all 3 deployment methods)

### 🚀 **Ready for Production?**
Read: **`DEPLOYMENT.md`** (cloud, docker, heroku guides)

---

## 📂 Project File Structure

```
maintenance-agent/
│
├── 📍 ENTRY POINTS (Pick One)
│   ├── app_with_embedded_api.py       ⭐ **START HERE** (Option 2)
│   │   └─ Single command: streamlit run app_with_embedded_api.py
│   ├── unified_app.py                 (Option 3 - Production)
│   │   └─ Single command: streamlit run unified_app.py
│   └── maintenance_agent_backend.py   (Backend core)
│       ├─ FastAPI server
│       ├─ Vision stub (needs real VLM)
│       ├─ RAG index
│       └─ SQLite logging
│
├── 📁 app/
│   └── maintenance_agent_frontend.py  (Option 1 - Separate)
│       └─ Original Streamlit frontend
│
├── 📁 vision/
│   └── vision.py                      (Placeholder)
│       └─ TODO: Integrate real VLM
│
├── 📁 rag/
│   └── rag.py                         (Placeholder)
│       └─ Core logic in backend.py
│
├── 📁 manuals/                        (User's PDFs for RAG)
│   ├── pump_manual.pdf                (you add these)
│   └── hydraulic_system.pdf
│
├── 📁 logs/                           (Auto-created)
│   ├── maintenance_logs.db            ← SQLite database
│   └── 2025-11-26T10-30...OK.png      ← Logged images
│
├── 📁 .github/
│   └── copilot-instructions.md        (AI Agent guide)
│
├── 📚 DOCUMENTATION
│   ├── START_HERE.md                  ⭐ Read first
│   ├── QUICKSTART.md                  Quick commands
│   ├── ARCHITECTURE.md                Deployment diagrams
│   ├── DEPLOYMENT.md                  Cloud/Docker guide
│   ├── SETUP_COMPLETE.md              What was built
│   ├── README.md                      Original project info
│   └── (this file)
│
├── ⚙️ CONFIGURATION
│   └── requirements.txt               Python dependencies
│
└── 📊 DATA
    └── manual_index.npz               Cached embeddings
        └─ Auto-created on first run
```

---

## 📖 Documentation by Purpose

### 🚀 **Getting Started**
| File | Purpose | Read Time |
|------|---------|-----------|
| **START_HERE.md** | What to do right now | 5 min |
| **QUICKSTART.md** | Common commands reference | 3 min |
| **ARCHITECTURE.md** | Visual diagrams of 3 options | 10 min |

### 🔍 **Understanding the Project**
| File | Purpose | Read Time |
|------|---------|-----------|
| **README.md** | Original project description | 10 min |
| **.github/copilot-instructions.md** | Code architecture & patterns | 15 min |
| **SETUP_COMPLETE.md** | Complete summary of changes | 10 min |

### 🌐 **Deployment & Production**
| File | Purpose | Read Time |
|------|---------|-----------|
| **DEPLOYMENT.md** | Cloud/Docker/Heroku guides | 20 min |
| **QUICKSTART.md** | Local testing before deploy | 5 min |

---

## 🎬 Deployment Options at a Glance

### Option 1: Separate Processes (Development)
**Files involved:**
- `maintenance_agent_backend.py` (port 8000)
- `app/maintenance_agent_frontend.py` (port 8501)

**Start:**
```bash
# Terminal 1
python maintenance_agent_backend.py

# Terminal 2
streamlit run app/maintenance_agent_frontend.py
```

**When to use:** Debugging, development, independent testing

**Read:** QUICKSTART.md (Option 1 section)

---

### Option 2: Streamlit Auto-Launches Backend ⭐ RECOMMENDED
**Files involved:**
- `app_with_embedded_api.py` (only file)
- Automatically starts `maintenance_agent_backend.py` as subprocess

**Start:**
```bash
streamlit run app_with_embedded_api.py
```

**When to use:** Quick start, single-machine deployment, learning

**Read:** QUICKSTART.md (Option 2 section) or ARCHITECTURE.md (Option 2 diagram)

---

### Option 3: Unified Single-Process (Production)
**Files involved:**
- `unified_app.py` (all-in-one file)

**Start:**
```bash
streamlit run unified_app.py
```

**When to use:** Production, containers, cloud deployment, Streamlit Cloud

**Read:** DEPLOYMENT.md (entire file) or ARCHITECTURE.md (Option 3 diagram)

---

## 🔑 Key Files & Their Purpose

### Backend Core
- **`maintenance_agent_backend.py`** (377 lines)
  - FastAPI server
  - Vision stub (replace with real VLM)
  - RAG index (sentence-transformers)
  - SQLite logging
  - Supports FASTAPI_PORT env var (new!)

### Frontend Options
- **`app_with_embedded_api.py`** (NEW - 170 lines)
  - Streamlit UI
  - Auto-launches backend
  - Best for quick start

- **`app/maintenance_agent_frontend.py`** (113 lines)
  - Original Streamlit UI
  - Calls separate backend API
  - Best for development

- **`unified_app.py`** (NEW - 450+ lines)
  - Combined Streamlit + FastAPI
  - All-in-one deployment
  - Best for production

### Configuration
- **`requirements.txt`**
  - All Python dependencies
  - No changes needed (unchanged)

### Documentation
- **`.github/copilot-instructions.md`**
  - Architecture patterns
  - API contract
  - Code conventions
  - For AI agents

---

## 🎯 Common Workflows

### "I want to run it right now"
```bash
streamlit run app_with_embedded_api.py
# Open http://localhost:8501
```
📖 Read: QUICKSTART.md

---

### "I want to debug the backend"
```bash
# Terminal 1
python maintenance_agent_backend.py

# Terminal 2
streamlit run app/maintenance_agent_frontend.py
```
📖 Read: DEPLOYMENT.md (Option 1 section)

---

### "I want to deploy to Streamlit Cloud"
```bash
# 1. Push to GitHub
# 2. Go to https://share.streamlit.io
# 3. Deploy unified_app.py
```
📖 Read: DEPLOYMENT.md (Streamlit Cloud section)

---

### "I want to deploy to Docker/Heroku"
```bash
docker build -t maintenance-agent .
docker run -p 8501:8501 maintenance-agent
```
📖 Read: DEPLOYMENT.md (Docker/Heroku section)

---

### "I want to replace the vision stub with GPT-4o"
Edit `maintenance_agent_backend.py`, function `call_vlm_stub()`
📖 Read: .github/copilot-instructions.md (Section 4)

---

### "I want to add my own PDF manuals"
```bash
cp my_manual.pdf manuals/
rm manual_index.npz  # Forces rebuild
# Restart the app - index rebuilds automatically
```
📖 Read: QUICKSTART.md or DEPLOYMENT.md

---

## 📊 Changes Made (Summary)

| Type | File | Change |
|------|------|--------|
| ✅ New | `app_with_embedded_api.py` | Subprocess-based integration (Option 2) |
| ✅ New | `unified_app.py` | All-in-one Streamlit + FastAPI (Option 3) |
| ✅ New | `DEPLOYMENT.md` | Complete deployment guide |
| ✅ New | `ARCHITECTURE.md` | Visual diagrams |
| ✅ New | `QUICKSTART.md` | Quick reference |
| ✅ New | `START_HERE.md` | This file |
| ✅ New | `SETUP_COMPLETE.md` | Setup summary |
| ✅ New | `.github/copilot-instructions.md` | (Already existed - preserved) |
| 🔧 Modified | `maintenance_agent_backend.py` | Added FASTAPI_PORT env var support |

**No breaking changes!** Original files untouched and fully functional.

---

## ❓ FAQ by Documentation

**Q: "How do I start?"**
→ See START_HERE.md

**Q: "What are the 3 options?"**
→ See ARCHITECTURE.md

**Q: "How do I deploy to cloud?"**
→ See DEPLOYMENT.md

**Q: "What commands do I need?"**
→ See QUICKSTART.md

**Q: "How is this code structured?"**
→ See .github/copilot-instructions.md

**Q: "What was actually built?"**
→ See SETUP_COMPLETE.md

---

## 🚀 Quick Navigation

| I want to... | Go to... |
|---|---|
| Run the app now | `START_HERE.md` |
| Understand options | `ARCHITECTURE.md` |
| Deploy to cloud | `DEPLOYMENT.md` |
| Reference commands | `QUICKSTART.md` |
| Understand code | `.github/copilot-instructions.md` |
| See changes | `SETUP_COMPLETE.md` |

---

## ✅ What's Ready to Use

- ✅ Option 1: Separate backend + frontend processes
- ✅ Option 2: Auto-launched FastAPI from Streamlit ⭐
- ✅ Option 3: All-in-one unified app
- ✅ Environment variable support for ports
- ✅ Full documentation for all scenarios
- ✅ Deployment guides for cloud platforms

---

## 🎓 Next Steps

1. **Run it:** `streamlit run app_with_embedded_api.py`
2. **Test it:** Upload an image at http://localhost:8501
3. **Customize it:** Replace vision stub, add PDFs
4. **Deploy it:** Follow DEPLOYMENT.md for your platform

---

**Everything is set up and ready to go!** 🎉

Start with `START_HERE.md` or run the command above.
