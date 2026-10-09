# What To Do Now — LipiAI Setup Guide

Everything you need to run, fix, and understand this project.

---

## Project Structure

```
leapy/
├── frontend/                         ← React app (TanStack Start + Vite + Tailwind)
│   ├── src/
│   │   ├── routes/
│   │   │   ├── index.tsx             ← Home page (/)
│   │   │   ├── dashboard.tsx         ← Inscription analysis (/dashboard)
│   │   │   ├── about.tsx             ← About page (/about)
│   │   │   └── chat.tsx              ← Chat page (/chat)
│   │   ├── components/
│   │   │   ├── chat-interface.tsx    ← Full chat UI
│   │   │   └── lipiAI-shell.tsx      ← Site shell (nav + footer)
│   │   └── lib/
│   │       ├── chat-service.ts       ← Calls backend API
│   │       └── inscription-analysis.ts
│   ├── .env                          ← Frontend env vars (already created)
│   └── vite.config.ts
│
├── backend/                          ← Python Flask server
│   ├── app.py                        ← All endpoints
│   ├── gemini_client.py              ← Google Gemini AI
│   ├── translator.py                 ← Google Translate (Nepali → Nepal Bhasa)
│   ├── script_converter.py           ← aksharamukha (Devanagari → Ranjana)
│   ├── .env                          ← Your API key lives here
│   ├── .env.example                  ← Template
│   ├── requirements.txt
│   └── start.bat                     ← Double-click to start on Windows
│
└── what_to_do_now.md                 ← This file
```

---

## How the Chat Pipeline Works

Gemini **cannot speak Nepal Bhasa (Newari) natively**. So the app uses a
3-step pipeline where each step is only applied when needed:

```
User message (Devanagari)
        │
        ▼
[Step 1]  Google Gemini
          → Always replies in NEPALI (Devanagari)
          → Model: models/gemini-3.5-flash
        │
        ▼
[Step 2]  Google Translate       (Nepal Bhasa modes only)
          → Nepali (ne) → Nepal Bhasa / Newari (new)
          → Skipped for pure Nepali modes
        │
        ▼
[Step 3]  aksharamukha           (Ranjana modes only)
          → Devanagari → Ranjana script
          → Output uses Tibetan Unicode, rendered by RanjanaUNICODE font
          → Skipped for Devanagari modes
        │
        ▼
Response shown to user
```

### The three chat modes

| Mode | Language | Script | Step 2 | Step 3 |
|------|----------|--------|--------|--------|
| `nepal-bhasa-devanagari` | Nepal Bhasa | Devanagari | ✅ Yes | ❌ No |
| `nepali-ranjana` | Nepali | Ranjana | ❌ No | ✅ Yes |
| `nepal-bhasa-ranjana` | Nepal Bhasa | Ranjana | ✅ Yes | ✅ Yes |

---

## How to Run Everything (Every Time)

You need **two terminals open** whenever you use the app.

### Terminal 1 — Start the backend

```
cd C:\Users\bipul\OneDrive\Desktop\leapy\backend
python app.py
```

You should see:
```
Gemini ready  model=models/gemini-3.5-flash
Starting LipiAI backend on port 5001
 * Running on http://127.0.0.1:5001
```

Keep this open. Verify at: http://localhost:5001/health
Expected: `{"gemini_configured": true, "model": "models/gemini-3.5-flash", "status": "ok"}`

### Terminal 2 — Start the frontend

```
cd C:\Users\bipul\OneDrive\Desktop\leapy\frontend
npm run dev
```

Open: **http://localhost:3000**
Click **Chat** in the top navigation.

---

## Your API Key

Your Gemini API key is in:
```
C:\Users\bipul\OneDrive\Desktop\leapy\backend\.env
```

```
GEMINI_API_KEY=AQ.Ab8RN6...   ← your key (already set)
GEMINI_MODEL=models/gemini-3.5-flash
PORT=5001
FRONTEND_ORIGIN=http://localhost:3000
```

The frontend `.env` at `leapy/frontend/.env` contains:
```
VITE_LIPIAI_CHAT_URL=http://localhost:5001
VITE_LIPIAI_ANALYSIS_URL=http://localhost:5001/api/analyze
```

**Rule:** API key only ever goes in `backend/.env`. Never in the frontend.

---

## Troubleshooting

### "Failed to fetch"
The frontend cannot reach the backend server.

Checklist:
1. Is the backend running? Open http://localhost:5001/health — you must see `"status": "ok"`
2. If not running: open a terminal → `cd leapy\backend` → `python app.py`
3. Did you restart the frontend after editing `.env`? Stop `npm run dev` and run it again.
4. Is `frontend/.env` set correctly?
   ```
   VITE_LIPIAI_CHAT_URL=http://localhost:5001
   ```

### "Backend URL not configured"
`VITE_LIPIAI_CHAT_URL` is empty or missing.

Fix: Open `leapy/frontend/.env` and make sure it says:
```
VITE_LIPIAI_CHAT_URL=http://localhost:5001
```
Then **restart the frontend dev server**.

### "AI service error: 503 model overloaded"
The Gemini API is temporarily overloaded. The backend retries once automatically.
If it keeps happening, wait 30 seconds and try again.

### "AI service error: 404 model not found"
The Gemini model name is wrong or unavailable for your API key.

Fix:
1. Open `leapy/backend/.env`
2. Change `GEMINI_MODEL=` to `models/gemini-3.5-flash`
3. Restart the backend

To list models available to your key, run from `leapy/backend/`:
```
python -c "
from dotenv import load_dotenv; import os; load_dotenv()
from google import genai
client = genai.Client(api_key=os.environ['GEMINI_API_KEY'])
for m in client.models.list():
    if 'gemini' in m.name and 'flash' in m.name:
        print(m.name)
"
```

### "gemini_configured: false" at /health
The backend started without finding the `.env` file.

Fix: Always run `python app.py` from INSIDE `leapy/backend/`, not from another folder.

### Ranjana text shows as boxes (□□□)
The Ranjana font is not loading.

The font is declared in `frontend/src/styles.css` via `@font-face`.
Also Noto Serif Tibetan loads from Google Fonts as a fallback.
Make sure you have an internet connection on first load.

### Nepal Bhasa sounds like Nepali
This is a known limitation of Google Translate's `new` (Newari) language support.
The translate step is best-effort — if it returns empty or fails, the app
falls back to the Nepali Gemini reply rather than crashing.

---

## Backend API Reference

Base URL: `http://localhost:5001`

### GET /health
```json
{ "status": "ok", "gemini_configured": true, "model": "models/gemini-3.5-flash" }
```

### POST /api/chat
```json
// Request
{
  "messages": [
    { "role": "user",      "text": "नमस्ते" },
    { "role": "assistant", "text": "नमस्ते!" },
    { "role": "user",      "text": "तपाईंको नाम के हो?" }
  ],
  "mode": "nepali-ranjana"
}

// Response
{
  "content":            "ནམསྟེ།",   ← display text (in Ranjana or Devanagari)
  "content_devanagari": "नमस्ते।",  ← always Devanagari (store for AI history)
  "script":             "ranjana",
  "mode":               "nepali-ranjana"
}
```

### POST /api/convert  (standalone script conversion)
```json
// Request:  { "text": "नमस्ते", "target": "ranjana" }
// Response: { "result": "ནམསྟེ", "target": "ranjana" }
// targets:  "devanagari" | "newa" | "ranjana"
```

### POST /api/translate  (standalone language translation)
```json
// Request:  { "text": "नमस्ते", "source": "ne", "target": "new" }
// Response: { "result": "...", "source": "ne", "target": "new" }
```

### POST /api/analyze  (inscription image)
```
multipart/form-data  field: image
Response: { "translation": "...", "summary": "..." }
```

---

## Files That Must Never Be Committed to Git

```
leapy/backend/.env     ← contains GEMINI_API_KEY
leapy/frontend/.env    ← safe but private by convention
```

Both are in `.gitignore`. Never commit them.
