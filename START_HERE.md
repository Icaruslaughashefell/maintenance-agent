# 🚀 Start Here - Next Steps

Your Maintenance Agent is now ready for **3 different deployment options**!

## 🎯 What Just Got Built

You asked: *"I need to deploy on Streamlit as FastAPI"*

**Answer:** Three ways to run FastAPI inside (or alongside) Streamlit:

| # | Name | Start Command | Best For |
|---|------|---------------|----------|
| 1 | **Separate Processes** | 2 terminals | Development/Debugging |
| 2 | **Streamlit + Auto-Launched Backend** | `streamlit run app_with_embedded_api.py` | 👈 **START HERE** |
| 3 | **Unified Single-Process** | `streamlit run unified_app.py` | Production/Containers |

---

## ⚡ Quick Start (Recommended)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run the App (One Command!)
```bash
streamlit run app_with_embedded_api.py
```

### Step 3: Open Browser
Streamlit will automatically open:
```
http://localhost:8501
```

**That's it!** FastAPI starts automatically on port 8001 in the background.

---

## 📁 New Files Created

### Core Apps
- **`app_with_embedded_api.py`** ← **Use this one first** (Option 2)
- `unified_app.py` (Option 3, for production)
- Modified `maintenance_agent_backend.py` (now accepts FASTAPI_PORT env var)

### Documentation
- **`QUICKSTART.md`** ← Quick reference for commands
- **`DEPLOYMENT.md`** ← Detailed scenarios (cloud, docker, heroku)
- **`ARCHITECTURE.md`** ← Visual diagrams of all 3 options
- **`SETUP_COMPLETE.md`** ← Complete summary of what was done
- `.github/copilot-instructions.md` ← Existing (AI agent guide)

---

## 🎬 Test It Now

Once running at http://localhost:8501:

1. **Click "Choose an image"** → Upload any machine/component photo
2. **Optional**: Add a question (e.g., "I hear a clicking sound")
3. **Click "🔍 Analyze"** → Wait 3-5 seconds
4. **See Results**:
   - Status: OK or NG
   - Defect type detected
   - Confidence score
   - Recommended actions
   - Reference manuals from PDFs

---

## 🔄 Understanding the 3 Options

### Option 1: Separate Processes
```bash
# Terminal 1
python maintenance_agent_backend.py
# Runs on http://localhost:8000

# Terminal 2 (different terminal window)
streamlit run app/maintenance_agent_frontend.py
# Runs on http://localhost:8501
```
✅ Best for debugging  
❌ Requires 2 windows

---

### Option 2: Auto-Launched Backend (RECOMMENDED)
```bash
streamlit run app_with_embedded_api.py
# Everything starts automatically
# Opens http://localhost:8501
```
✅ Single command  
✅ Simple setup  
✅ Beginner-friendly  
✅ One terminal window

---

### Option 3: All-in-One (Production)
```bash
streamlit run unified_app.py
# True single-process deployment
# Best for Docker/Heroku/Streamlit Cloud
```
✅ Best for containers  
✅ Best for production  
✅ Smallest footprint  
❌ More complex to debug

---

## 📊 Comparison Table

| Feature | Option 1 | Option 2 | Option 3 |
|---------|:---:|:---:|:---:|
| **Start ease** | 🟡🟡 | 🟢🟢🟢 | 🟢🟢🟢 |
| **Debug ease** | 🟢🟢🟢 | 🟢🟢 | 🟡 |
| **Single command** | ❌ | ✅ | ✅ |
| **Works locally** | ✅ | ✅ | ✅ |
| **Streamlit Cloud** | ❌ | ❌ | ✅ |
| **Docker/Heroku** | ⚠️ | ⚠️ | ✅ |

---

## 🚀 Next: Deployment to Cloud

Once you're happy with local testing:

### **Streamlit Cloud** (Free)
```bash
# Using Option 3 (unified_app.py)
# 1. Push to GitHub
# 2. Go to https://share.streamlit.io
# 3. Deploy unified_app.py
# Done! Public URL: https://your-app-xyz.streamlit.app
```

### **Docker** (Any cloud)
```bash
# Using Option 3 (unified_app.py)
docker build -t maintenance-agent .
docker run -p 8501:8501 maintenance-agent
```

### **Heroku** (Legacy)
```bash
# Using Procfile + Dockerfile
heroku create your-app-name
git push heroku main
```

---

## 🎓 Common Next Steps

### 1. Replace the Vision Stub
Currently the app returns **random** defects for testing. To use a real AI model:

```python
# In maintenance_agent_backend.py, replace call_vlm_stub()
def call_vlm_stub(image_base64: str, question: Optional[str] = None):
    # OPTION A: Use OpenAI GPT-4 Vision
    # OPTION B: Use Google Gemini Vision
    # OPTION C: Use Anthropic Claude Vision
    # See copilot-instructions.md for examples
    pass
```

### 2. Add PDF Manuals
```bash
# 1. Place PDFs in the manuals/ folder
cp ~/Downloads/pump_manual.pdf manuals/
cp ~/Downloads/hydraulic_guide.pdf manuals/

# 2. Delete the cache (forces rebuild)
rm manual_index.npz

# 3. Restart the app
streamlit run app_with_embedded_api.py
# App will rebuild index from new PDFs on startup
```

### 3. Customize the Defect Types
Edit `call_vlm_stub()` to return different defect categories:
```python
defect_candidates = [
    "normal",
    "rust_on_pipe",
    "oil_leak",
    "loose_bolt",
    # Add your defects here
    "cracked_bearing",
    "misalignment",
    "corrosion"
]
```

### 4. Monitor Logged Data
```bash
# View analyzed images
ls logs/

# Query the database
sqlite3 logs/maintenance_logs.db
> SELECT * FROM logs;
> .mode column
> .headers on
```

---

## ⚠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| **"Cannot connect to backend"** | Wait 3 seconds after Streamlit starts |
| **"Port 8001 already in use"** | `lsof -ti:8001 \| xargs kill -9` |
| **Backend doesn't respond** | Check `logs/` folder for errors |
| **Image upload fails** | Ensure file < 10MB, format: jpg/jpeg/png |
| **No manuals found** | Add PDFs to `manuals/` folder, restart |

---

## 📚 Documentation Map

```
START HERE
    ↓
├─ QUICKSTART.md          ← Quick commands & common tasks
├─ SETUP_COMPLETE.md      ← What was done & why
├─ ARCHITECTURE.md        ← Visual diagrams of all 3 options
├─ DEPLOYMENT.md          ← Cloud/Docker/Heroku deployment
│
└─ For AI Agents:
   └─ .github/copilot-instructions.md ← Code patterns & architecture
```

---

## 🎉 You're Ready!

```bash
# Run this now:
streamlit run app_with_embedded_api.py

# Then open: http://localhost:8501
```

**Questions?** Check:
- `QUICKSTART.md` for common commands
- `ARCHITECTURE.md` for how it all fits together
- `DEPLOYMENT.md` for production setups
- `.github/copilot-instructions.md` for code patterns

---

**Happy deploying!** 🚀
