# Quick Start: Deploy Streamlit + FastAPI

## Installation

```bash
pip install -r requirements.txt
```

## Run Now (Choose One)

### ✅ **Recommended: Single Command (Option 2)**
```bash
streamlit run app_with_embedded_api.py
```
Opens at: http://localhost:8501
- FastAPI runs on port 8001 automatically
- Most beginner-friendly

---

### Development: Two Separate Terminals (Option 1)
```bash
# Terminal 1:
python maintenance_agent_backend.py
# http://localhost:8000

# Terminal 2:
streamlit run app/maintenance_agent_frontend.py
# http://localhost:8501
```
- Better for debugging
- Easier to iterate on each component

---

### Advanced: Unified Single-Process (Option 3)
```bash
streamlit run unified_app.py
```
- Best for production/containers
- Runs everything in one process

---

## What These Files Do

| File | Purpose |
|------|---------|
| `maintenance_agent_backend.py` | FastAPI backend (analysis API) |
| `app/maintenance_agent_frontend.py` | Streamlit UI (original, separate API) |
| `app_with_embedded_api.py` | **NEW** – Streamlit UI that auto-starts backend |
| `unified_app.py` | **NEW** – All-in-one Streamlit + FastAPI |
| `DEPLOYMENT.md` | Detailed deployment guide |

---

## Testing the API Directly

If using separate backend:

```bash
# Get a test image as base64
python3 -c "
import base64
with open('test.png', 'rb') as f:
    print(base64.b64encode(f.read()).decode())
" > test_b64.txt

# Call API
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "image_base64": "'$(cat test_b64.txt)'",
    "client_id": "test-machine"
  }' | jq .
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Connection refused" on port 8001 | Wait 3 seconds after Streamlit starts |
| "Port already in use" | Kill existing process: `lsof -ti:8001 \| xargs kill -9` |
| Backend not responding | Check `logs/` folder for error messages |
| Image upload fails | Ensure image is < 10MB |

---

## Next Steps

1. **Add real VLM**: Replace `call_vlm_stub()` in backend with GPT-4o/Claude/Gemini
2. **Add PDFs**: Place manuals in `manuals/` folder, restart to rebuild index
3. **Deploy**: See `DEPLOYMENT.md` for Streamlit Cloud / Docker / Heroku instructions
4. **Customize**: Edit prompts in `build_vision_prompt()` or defect types

---

For more details, see `DEPLOYMENT.md`
