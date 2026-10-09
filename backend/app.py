"""
app.py  —  LipiAI backend
--------------------------
Pipeline for every chat message:

  User input (Devanagari)
      │
      ▼
  [1] Gemini  →  always replies in Nepali (Devanagari)
      │             Gemini cannot speak Nepal Bhasa natively,
      │             so we always generate Nepali first.
      │
      ▼
  [2] Google Translate  →  Nepali → Nepal Bhasa  (only for nepal-bhasa-* modes)
      │                    Uses deep-translator / Google Translate API
      │                    Language codes: ne (Nepali) → new (Newari/Nepal Bhasa)
      │
      ▼
  [3] aksharamukha  →  Devanagari → Ranjana  (only for *-ranjana modes)
      │                Uses the aksharamukha Python package.
      │                Ranjana output uses Tibetan Unicode rendered by
      │                the RanjanaUNICODE font loaded in the frontend.
      │
      ▼
  Response: { content (display), content_devanagari (for history), script, mode }
"""

import os
import logging
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from dotenv import load_dotenv

import gemini_client
import script_converter
import translator

# ── Environment ────────────────────────────────────────────────────────────────
load_dotenv()

GEMINI_API_KEY  = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL    = os.environ.get("GEMINI_MODEL", "models/gemini-3.5-flash")
PORT            = int(os.environ.get("PORT", 5001))
FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "http://localhost:3000")

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

# ── Flask ──────────────────────────────────────────────────────────────────────
app = Flask(__name__)
# Allow any localhost port — works regardless of which port Vite picks (3000, 8080, etc.)
CORS(app, origins="*", supports_credentials=False)

# ── Gemini ─────────────────────────────────────────────────────────────────────
if GEMINI_API_KEY:
    gemini_client.configure(GEMINI_API_KEY)
    log.info("Gemini ready  model=%s", GEMINI_MODEL)
else:
    log.warning("GEMINI_API_KEY not set — AI features disabled.")

# ── Mode → target script mapping ───────────────────────────────────────────────
#
#  nepal-bhasa-devanagari : Gemini(Nepali) → Translate(Nepal Bhasa) → show Devanagari
#  nepali-ranjana         : Gemini(Nepali) → aksharamukha(Ranjana)
#  nepal-bhasa-ranjana    : Gemini(Nepali) → Translate(Nepal Bhasa) → aksharamukha(Ranjana)
#
VALID_MODES: dict[str, str] = {
    "nepal-bhasa-devanagari": "devanagari",
    "nepali-ranjana":         "ranjana",
    "nepal-bhasa-ranjana":    "ranjana",
}
NEPAL_BHASA_MODES = {"nepal-bhasa-devanagari", "nepal-bhasa-ranjana"}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _error(msg: str, status: int = 400) -> tuple[Response, int]:
    log.warning("HTTP %d: %s", status, msg)
    return jsonify({"error": msg}), status


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/health")
def health() -> tuple[Response, int]:
    return jsonify({
        "status": "ok",
        "gemini_configured": bool(GEMINI_API_KEY),
        "model": GEMINI_MODEL,
    }), 200


@app.post("/api/chat")
def chat() -> tuple[Response, int]:
    """
    Main chat endpoint.

    Request body:
      {
        "messages": [{"role": "user"|"assistant", "text": "..."}],
        "mode": "nepal-bhasa-devanagari" | "nepali-ranjana" | "nepal-bhasa-ranjana"
      }

    Response:
      {
        "content":            "...",   // text in display script (show to user)
        "content_devanagari": "...",   // Devanagari text (store for AI history)
        "script":             "devanagari" | "ranjana",
        "mode":               "..."
      }
    """
    if not GEMINI_API_KEY:
        return _error(
            "Chat service not configured. Set GEMINI_API_KEY in backend/.env.",
            503,
        )

    body = request.get_json(silent=True)
    if not body:
        return _error("Request body must be JSON.")

    messages: list[dict] = body.get("messages", [])
    mode_id: str         = body.get("mode", "")

    if not messages:
        return _error("'messages' cannot be empty.")
    if mode_id not in VALID_MODES:
        return _error(f"Invalid mode '{mode_id}'. Valid: {list(VALID_MODES)}")

    for i, msg in enumerate(messages):
        if not isinstance(msg, dict):
            return _error(f"messages[{i}] must be an object.")
        if msg.get("role") not in ("user", "assistant"):
            return _error(f"messages[{i}].role must be 'user' or 'assistant'.")
        if not isinstance(msg.get("text"), str) or not msg["text"].strip():
            return _error(f"messages[{i}].text must be a non-empty string.")

    if messages[-1].get("role") != "user":
        return _error("Last message must have role 'user'.")

    target_script = VALID_MODES[mode_id]

    # ── Step 1: Gemini → Nepali Devanagari ────────────────────────────────────
    try:
        nepali_text = gemini_client.generate_reply(
            messages=messages,
            model_name=GEMINI_MODEL,
        )
        log.info("[%s] Gemini (Nepali): %s", mode_id, nepali_text[:100])
    except ValueError as e:
        return _error(str(e), 400)
    except Exception as e:
        log.exception("Gemini error")
        return _error(f"AI service error: {e}", 502)

    # ── Step 2: Google Translate → Nepal Bhasa (Newari) if needed ────────────
    devanagari_text = nepali_text
    if mode_id in NEPAL_BHASA_MODES:
        try:
            nb_text = translator.nepali_to_nepal_bhasa(nepali_text)
            if nb_text and nb_text.strip():
                devanagari_text = nb_text
                log.info("[%s] Translated to Nepal Bhasa: %s", mode_id, devanagari_text[:100])
            else:
                log.warning("[%s] Translation returned empty, keeping Nepali", mode_id)
        except Exception as e:
            log.warning("[%s] Translation failed (%s), keeping Nepali", mode_id, e)
            # Graceful fallback: show Nepali if Nepal Bhasa translation fails

    # ── Step 3: Ranjana visual rendering ───────────────────────────────────────
    # The Nithya Ranjana DU font uses Devanagari Unicode codepoints and renders
    # them as Ranjana/Lantsa glyphs via OpenType GSUB rules — no text conversion
    # needed. We pass the Devanagari text unchanged; the browser applies the font.
    display_text = devanagari_text
    if target_script == "ranjana":
        log.info("[%s] Ranjana (font-rendered Devanagari): %s", mode_id, display_text[:60])

    return jsonify({
        "content":            display_text,
        "content_devanagari": devanagari_text,
        "script":             target_script,
        "mode":               mode_id,
    }), 200


@app.post("/api/convert")
def convert_endpoint() -> tuple[Response, int]:
    """Standalone script conversion utility."""
    body = request.get_json(silent=True)
    if not body:
        return _error("Request body must be JSON.")
    text   = body.get("text", "")
    target = body.get("target", "")
    if not text:
        return _error("'text' is required.")
    if target not in ("devanagari", "newa", "ranjana"):
        return _error("'target' must be: devanagari | newa | ranjana.")
    result = script_converter.convert_script(text, target)
    return jsonify({"result": result, "target": target}), 200


@app.post("/api/translate")
def translate_endpoint() -> tuple[Response, int]:
    """Standalone language translation utility."""
    body = request.get_json(silent=True)
    if not body:
        return _error("Request body must be JSON.")
    text   = body.get("text", "")
    source = body.get("source", "auto")
    target = body.get("target", "")
    if not text:
        return _error("'text' is required.")
    if target not in ("ne", "new"):
        return _error("'target' must be 'ne' (Nepali) or 'new' (Nepal Bhasa).")
    result = translator.translate(text, source=source, target=target)
    return jsonify({"result": result, "source": source, "target": target}), 200


@app.post("/api/analyze")
def analyze_inscription() -> tuple[Response, int]:
    """Inscription image analysis via Gemini Vision."""
    if not GEMINI_API_KEY:
        return _error("Analysis service not configured.", 503)
    if "image" not in request.files:
        return _error("'image' file is required.")

    image_file = request.files["image"]
    if not image_file.content_type or not image_file.content_type.startswith("image/"):
        return _error("Uploaded file must be an image.")

    try:
        from google.genai import types as gt
        image_bytes = image_file.read()
        client = gemini_client._get_client()

        prompt = (
            "This image shows an inscription in a classical South Asian script "
            "(possibly Prachalit Newa, Devanagari, or Ranjana). Provide:\n"
            "1. A literal translation of the text.\n"
            "2. A brief summary of what it describes.\n\n"
            "Format exactly as:\n"
            "TRANSLATION: <translation>\n"
            "SUMMARY: <summary>"
        )

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[gt.Content(parts=[
                gt.Part(text=prompt),
                gt.Part(inline_data=gt.Blob(
                    mime_type=image_file.content_type,
                    data=image_bytes,
                )),
            ])],
            config=gt.GenerateContentConfig(temperature=0.3, max_output_tokens=1024),
        )

        text = response.text or ""
        translation = summary = ""
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("TRANSLATION:"):
                translation = line[len("TRANSLATION:"):].strip()
            elif line.startswith("SUMMARY:"):
                summary = line[len("SUMMARY:"):].strip()
        if not translation and not summary:
            translation = text

        return jsonify({"translation": translation, "summary": summary}), 200

    except Exception as e:
        log.exception("Inscription analysis error")
        return _error(f"Analysis failed: {e}", 502)


# ── Error handlers ─────────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method not allowed"}), 405

@app.errorhandler(500)
def server_error(e):
    log.exception("Internal server error")
    return jsonify({"error": "Internal server error"}), 500


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    log.info("Starting LipiAI backend on port %d", PORT)
    app.run(host="0.0.0.0", port=PORT, debug=False)




