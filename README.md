

# 🛠️🧌 Maintenance Agent — *the chaotic edition*

**“An AI that looks at your machines and goes: 🤨 babe… that’s broken.”**

Welcome to the most unhinged, half-baked-but-surprisingly-functional AI maintenance project ever created by sleep-deprived geniuses and LINE refugees.

---

## 🌪️ What IS this???

It’s a little goblin system that:

1. **Sees** your machine (👁️ VLM braincell)
2. **Screams** when it finds rust, cracks, leaks, or ✨vibes✨
3. **Digs** into PDFs like a raccoon in a dumpster (📚 RAG)
4. **Returns** pretty JSON telling you how to fix stuff

Basically:

> *“AI but it’s also a mechanic with anxiety and poor social skills.”*

---

## 🗂️ Project Structure (affectionate)

```
maintenance-agent/
│
├── app/                # backend (FastAPI) — the adult of the group
│   └── main.py
│
├── streamlit_app/      # frontend (Streamlit) — the people pleaser
│   └── app.py
│
├── vision/             # VLM wrangler — keeps yelling "FORMAT YOUR JSON"
│   └── vision.py
│
├── rag/                # PDF goblin — eats manuals for breakfast
│   └── rag.py
│
├── data/
│   ├── manuals/        # PDFs (aka "grandma's recipe for fixing machines")
│   └── images/         # test pics (please no selfies)
│
├── requirements.txt
└── README.md           # this beautiful mess
```

---

## 🦾 Backend (FastAPI):

The “responsible eldest sibling” of the family.

* Takes your base64 image
* Calls Vision goblin
* Calls RAG raccoon
* Returns JSON like a polite citizen
* Doesn’t throw hands (usually)

Run it with:

```bash
uvicorn app.main:app --reload
```

Backend lives at:
👉 `http://localhost:8000`
Like a shy kid sitting in the corner.

---

## 🎨 Frontend (Streamlit):

The ✨aesthetic✨ part of the project.

* Let you upload images
* Sends your cursed pictures to backend
* Shows JSON results
* Will absolutely judge your image quality

Run it with:

```bash
streamlit run streamlit_app/app.py
```

Frontend opens:
👉 `http://localhost:8501`
Where all the magic (and suffering) happens.

---

## 👁️ Vision Module (aka “AI, pls behave”)

This thing:

* Calls GPT-4o / Gemini / whatever deity you appease
* Detects defects
* Reads gauges (IF IT FEELS LIKE IT)
* Returns JSON only.
  (**Respond-in-JSON-or-you-die** energy)

Lives in:
`vision/vision.py`

---

## 📚 RAG Module (the raccoon)

This one:

* Tears PDFs into chunks
* Builds vector index
* For each defect, digs into manuals like trash
* Returns repair procedures like:
  “tighten bolt using tool #6 or perish.”

Lives in:
`rag/rag.py`

---

## 🔥 Phase 2 Status

Things we *are* doing:

* building Vision logic
* building RAG logic
* building API skeleton
* giggling
* crying
* threatening Streamlit

Things we are **NOT** doing:

* using LINE as version control EVER AGAIN
* writing documentation like normal people
* sleeping

---

## 🧑‍🎤 How to Contribute

1. Clone repo
2. Make a branch
3. Commit chaos
4. PR
5. Pray

**Do NOT upload code in LINE.**
If you do, a developer fairy dies. 🧚💀

---

## 💖 Credits

Made by **da team**, a creature powered by:

* P' Jarbz
* AON
* Anfield
* Sia
* P'van
* P'bomb
* P'ohm
* minty
* P'brooky

---

## 😈 Final words

If this code runs: hooray.
If this code breaks: also hooray, because we’re learning ❤️
If the JSON formatting breaks: blame the AI, obviously.

---
