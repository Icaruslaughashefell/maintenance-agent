# 🚀 Quick Reference Card

## ⚡ TLDR - Just Run This

```bash
streamlit run app_with_embedded_api.py
```

Then open: **http://localhost:8501**

---

## 3️⃣ Deployment Options

```
┌────────────────────────────────────────────────────┐
│  Option 1: Separate Processes                      │
│  ─────────────────────────────────────────────     │
│  Terminal 1: python maintenance_agent_backend.py   │
│  Terminal 2: streamlit run app/...frontend.py      │
│  Best for: Development/Debugging                   │
└────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────┐
│  Option 2: Auto-Launch Backend ⭐ RECOMMENDED     │
│  ─────────────────────────────────────────────     │
│  streamlit run app_with_embedded_api.py            │
│  Best for: Quick Start                             │
└────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────┐
│  Option 3: All-in-One                              │
│  ─────────────────────────────────────────────     │
│  streamlit run unified_app.py                      │
│  Best for: Production/Cloud                        │
└────────────────────────────────────────────────────┘
```

---

## 📚 Documentation

| Need | Read | Time |
|------|------|------|
| **Get started NOW** | 00_READ_ME_FIRST.md | 3 min |
| **Understand options** | ARCHITECTURE.md | 10 min |
| **Deploy to cloud** | DEPLOYMENT.md | 20 min |
| **Quick commands** | QUICKSTART.md | 3 min |
| **Code patterns** | .github/copilot-instructions.md | 15 min |

---

## 🎬 First Time?

1. Install: `pip install -r requirements.txt`
2. Run: `streamlit run app_with_embedded_api.py`
3. Wait: ~3 seconds for FastAPI to start
4. Open: http://localhost:8501
5. Upload: A machine image
6. Click: "Analyze"
7. See: Results!

---

## 🔧 Common Commands

### Start App
```bash
# Easy (recommended)
streamlit run app_with_embedded_api.py

# Or separate backends
python maintenance_agent_backend.py          # Term 1
streamlit run app/maintenance_agent_frontend.py  # Term 2

# Or all-in-one
streamlit run unified_app.py
```

### Add PDFs
```bash
cp my_manual.pdf manuals/
rm manual_index.npz
# Restart app
```

### Check Database
```bash
sqlite3 logs/maintenance_logs.db
> SELECT * FROM logs;
```

### Kill Process
```bash
lsof -ti:8501 | xargs kill -9   # Streamlit
lsof -ti:8001 | xargs kill -9   # FastAPI
```

---

## 📂 Key Files

| File | Purpose |
|------|---------|
| `app_with_embedded_api.py` | **Option 2 - Use This** |
| `unified_app.py` | Option 3 - Production |
| `maintenance_agent_backend.py` | FastAPI backend |
| `requirements.txt` | Python dependencies |
| `manuals/` | Your PDF files go here |
| `logs/` | Database + images created here |

---

## 🌐 URLs When Running

```
Streamlit UI: http://localhost:8501
FastAPI Docs: http://localhost:8001/docs  (Option 1 only)
Backend API:  http://localhost:8000/analyze (Option 1 only)
             http://localhost:8001/analyze (Option 2/3)
```

---

## ❓ Quick Help

| Problem | Solution |
|---------|----------|
| "Port in use" | `lsof -ti:8501 \| xargs kill -9` |
| "Module not found" | `pip install -r requirements.txt` |
| "Connection refused" | Wait 3 seconds, try again |
| "No PDFs found" | Add files to `manuals/`, restart |

---

## 🚀 Deploy to Cloud

### Streamlit Cloud (Free)
```bash
# Push to GitHub, then:
# 1. https://share.streamlit.io
# 2. Deploy unified_app.py
# Done! Public URL created
```

### Docker (Any Cloud)
```bash
docker build -t maintenance-agent .
docker run -p 8501:8501 maintenance-agent
```

---

## 🎯 Next Steps

- [ ] Run the app once
- [ ] Test with a sample image
- [ ] Read ARCHITECTURE.md
- [ ] Replace vision stub with real VLM
- [ ] Add your PDFs to manuals/
- [ ] Deploy to cloud
- [ ] Monitor logs

---

## 📞 More Info

```
START HERE ──→ 00_READ_ME_FIRST.md
     ↓
PICK OPTION  ──→ ARCHITECTURE.md
     ↓
UNDERSTAND  ──→ QUICKSTART.md
     ↓
CUSTOMIZE   ──→ .github/copilot-instructions.md
     ↓
DEPLOY      ──→ DEPLOYMENT.md
```

---

## ✅ Status

- ✅ Code ready
- ✅ Documentation complete
- ✅ 3 deployment options working
- ✅ All dependencies in requirements.txt
- ✅ Ready to deploy

**Run it now!**

```bash
pip install -r requirements.txt
streamlit run app_with_embedded_api.py
```

🎉 Done!
