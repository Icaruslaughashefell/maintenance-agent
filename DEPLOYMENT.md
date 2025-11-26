# Deployment Guide: Streamlit with FastAPI

This guide shows **3 deployment options** for running the Maintenance Agent with Streamlit and FastAPI.

## Option 1: Separate Processes (Recommended for Development)

**Best for**: Local development, debugging, testing

Run two terminals side-by-side:

```bash
# Terminal 1: FastAPI backend
python maintenance_agent_backend.py
# Runs on http://localhost:8000

# Terminal 2: Streamlit frontend
streamlit run app/maintenance_agent_frontend.py
# Runs on http://localhost:8501
```

**Pros:**
- Easy to debug each component independently
- Hot reload works for both frontend and backend
- Simple to test API directly with curl/Postman

**Cons:**
- Requires two terminal windows
- Two separate processes to manage

---

## Option 2: Single Streamlit App with Embedded FastAPI Backend (Simple)

**Best for**: Single-machine deployment, no separate backend needed

```bash
streamlit run app_with_embedded_api.py
```

This app:
1. Starts FastAPI on port 8001 as a subprocess
2. Runs Streamlit UI on port 8501
3. Streamlit automatically calls the local API

**Pros:**
- Single command to start everything
- Single Streamlit URL to share
- Backend runs automatically

**Cons:**
- Slightly slower startup (waits for both to initialize)
- Subprocess management (not suitable for production containers)

---

## Option 3: Fully Unified FastAPI + Streamlit App (Advanced)

**Best for**: Single deployment package, production-ready

```bash
streamlit run unified_app.py
```

This app:
1. Merges all FastAPI logic into one Python file
2. Runs FastAPI in a background thread
3. Streamlit UI and API in the same process

**Pros:**
- True single-process deployment
- Smallest memory footprint
- Best for containerization

**Cons:**
- More complex debugging
- Threading (vs subprocess) can complicate error handling

---

## Deployment to Streamlit Cloud

To deploy to **Streamlit Cloud** (streamlit.io):

### Step 1: Prepare Repository
```bash
# Ensure you have a GitHub repo with these files:
requirements.txt
app_with_embedded_api.py (or unified_app.py)
maintenance_agent_backend.py
```

### Step 2: Update `requirements.txt`
Make sure all dependencies are listed:
```
fastapi
uvicorn
streamlit
requests
sentence-transformers
scikit-learn
pypdf
pillow
numpy
```

### Step 3: Deploy via Streamlit Cloud
1. Go to https://share.streamlit.io
2. Click "New app"
3. Connect your GitHub repo
4. Set main file path: `app_with_embedded_api.py`
5. Click "Deploy"

### Important Notes for Streamlit Cloud:
- **Port 8001** will NOT be accessible externally
- Use **Option 3 (unified_app.py)** instead – it runs API in same process
- Make sure `manuals/` folder is in your repo (or PDFs are downloaded at startup)
- `logs/` directory will be ephemeral (reset on redeploy)

---

## Deployment to Heroku / Railway / Cloud Run

For containerized deployment:

### Dockerfile
```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Use unified_app.py for single-process deployment
CMD ["streamlit", "run", "unified_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Procfile (Heroku)
```
web: streamlit run unified_app.py --server.port $PORT --server.address 0.0.0.0
```

### Environment Variables (if needed for VLM API keys)
```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-vision
```

---

## Quick Comparison Table

| Feature | Option 1 (Separate) | Option 2 (Subprocess) | Option 3 (Unified) |
|---------|:---:|:---:|:---:|
| **Single Command** | ❌ (2 terminals) | ✅ | ✅ |
| **Local Development** | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ |
| **Production Ready** | ❌ | ⚠️ | ✅ |
| **Streamlit Cloud** | ❌ | ❌ | ✅ |
| **Containerizable** | ✅ | ⚠️ | ✅ |
| **Debugging** | ✅ | ⚠️ | ⚠️ |

---

## Troubleshooting

### "Cannot connect to backend"
- **Separate mode**: Check that FastAPI is running on port 8000
- **Embedded mode**: Wait 5 seconds after Streamlit starts
- **Check port**: `lsof -i :8001` (macOS) or `netstat -ano | findstr :8001` (Windows)

### "Port already in use"
```bash
# Kill process on port 8001
lsof -ti:8001 | xargs kill -9  # macOS/Linux
# Or manually in Windows Task Manager
```

### "Module not found"
```bash
pip install -r requirements.txt
```

### FastAPI endpoint frozen
- Increase timeout in frontend: Change `timeout=60` to `timeout=120`
- Check backend logs for errors
- Try with a smaller image (large base64 strings can timeout)

---

## For Production: Recommendations

1. **Use Option 3 (unified_app.py)** for best compatibility
2. **Add authentication**: JWT or API key before exposing to internet
3. **Move logs to cloud storage** (S3, GCS) instead of local filesystem
4. **Use a real VLM** (replace stub in `call_vlm_stub()`)
5. **Set CORS properly**: Replace `allow_origins=["*"]` with specific domain
6. **Use environment variables** for API keys, model paths, etc.
7. **Monitor performance**: Add metrics logging for response times, error rates

---

## FAQ

**Q: Can I run this on a Raspberry Pi?**
A: Yes, but sentence-transformers model loading is slow. Pre-build embeddings and ship pre-computed index.

**Q: How do I scale this to multiple users?**
A: Use Option 1 (separate backend) with a real web framework, or multiple Streamlit cloud instances with shared database.

**Q: Can I integrate with a real VLM (GPT-4o, Claude, Gemini)?**
A: Yes! Replace `call_vlm_stub()` in the backend with actual API calls. See copilot-instructions.md for details.
