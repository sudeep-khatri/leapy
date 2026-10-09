# LipiAI Backend

Python/Flask backend for the LipiAI chat platform.

## What it does

| Step | Tool | Purpose |
|------|------|---------|
| 1 | **Google Gemini** | Generates replies in Nepal Bhasa or Nepali (always in Devanagari) |
| 2 | **Google Translate** (`deep-translator`) | Converts Gemini's Nepali drift back into Nepal Bhasa when needed |
| 3 | **aksharamukha** (Python package) | Converts Devanagari → Newa or Ranjana script before sending to frontend |

## Quick start

### 1. Get a Gemini API key
Go to https://aistudio.google.com/app/apikey and create a free key.

### 2. Create your .env file
```
cd leapy/backend
copy .env.example .env
```
Open `.env` and set:
```
GEMINI_API_KEY=your_key_here
```

### 3. Install dependencies
```
pip install -r requirements.txt
```

### 4. Run the server
```
python app.py
```
Or double-click `start.bat` on Windows.

The server starts on **http://localhost:5001**.

### 5. Configure the frontend
In `leapy/frontend/`, copy `.env.example` to `.env`:
```
VITE_LIPIAI_CHAT_URL=http://localhost:5001
VITE_LIPIAI_ANALYSIS_URL=http://localhost:5001/api/analyze
```

Then run the frontend:
```
cd leapy/frontend
npm run dev
```

Open http://localhost:3000 and navigate to /chat.

## API endpoints

### `POST /api/chat`
Main chat endpoint.
```json
// Request
{ "messages": [{"role": "user", "text": "नमस्ते"}], "mode": "nepal-bhasa-devanagari" }

// Response
{
  "content": "𑐣𑐩𑐳𑑂𑐟𑐾",          // display text (in chosen script)
  "content_devanagari": "नमस्ते",   // Devanagari intermediate
  "script": "newa",
  "mode": "nepal-bhasa-devanagari"
}
```

**Valid modes:**
- `nepal-bhasa-devanagari` — Nepal Bhasa in Devanagari
- `nepali-ranjana` — Nepali in Ranjana script
- `nepal-bhasa-ranjana` — Nepal Bhasa in Ranjana script

### `POST /api/convert`
Standalone script conversion.
```json
// Request
{ "text": "नमस्ते", "target": "newa" }
// Response
{ "result": "𑐣𑐩𑐳𑑂𑐟𑐾", "target": "newa" }
```

### `POST /api/translate`
Standalone language translation.
```json
// Request
{ "text": "नमस्ते", "source": "ne", "target": "new" }
// Response
{ "result": "...", "source": "ne", "target": "new" }
```

### `POST /api/analyze`
Inscription image analysis (multipart/form-data with `image` field).
```json
// Response
{ "translation": "...", "summary": "..." }
```

### `GET /health`
```json
{ "status": "ok", "gemini_configured": true, "model": "gemini-2.0-flash" }
```

## Environment variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | Yes | — | Your Google Gemini API key |
| `GEMINI_MODEL` | No | `gemini-2.0-flash` | Gemini model name |
| `PORT` | No | `5001` | Port to listen on |
| `FRONTEND_ORIGIN` | No | `http://localhost:3000` | Allowed CORS origin |

## Script conversion notes

- **Newa** (Nepal Bhasa traditional script): Unicode block U+11400–U+1147F, supported by Noto Sans Newa font
- **Ranjana** (Lantsa style): Uses Tibetan Unicode codepoints (U+0F00+) rendered as Ranjana glyphs by the RanjanaUNICODE font loaded in the frontend
- Conversion uses the `aksharamukha` Python package (installed via pip, not copied from source — GPL compliant)
- If conversion fails, the Devanagari text is returned unchanged as a graceful fallback
