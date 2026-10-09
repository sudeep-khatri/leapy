"""
app.py  —  LipiAI backend
--------------------------
Full pipeline for Nepal Bhasa modes:

  User types in Nepal Bhasa (Devanagari)
      │
      ▼
  [Step 0 — INPUT, Nepal Bhasa modes only]
      Gemini translates: Nepal Bhasa → Nepali
      (Google Translate does not support Nepal Bhasa 'new' language code)
      │
      ▼
  [Step 1]
      Gemini answers the Nepali question → Nepali reply
      │
      ▼
  [Step 2 — OUTPUT, Nepal Bhasa modes only]
      Gemini translates: Nepali reply → Nepal Bhasa
      │
      ▼
  [Step 3 — Ranjana modes only]
      NithyaRanjanaDU font renders Devanagari visually as Ranjana/Lantsa
      (No text conversion — the font does it via OpenType GSUB rules)
      │
      ▼
  Response: { content, content_devanagari, script, mode }

For Nepali modes (nepali-ranjana):
  User types Nepali → Gemini answers in Nepali → font renders as Ranjana
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
GEMINI_TRANSLATE_MODEL = os.environ.get("GEMINI_TRANSLATE_MODEL", "models/gemini-flash-lite-latest")
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
CORS(app, origins="*", supports_credentials=False)

# ── Gemini ─────────────────────────────────────────────────────────────────────
if GEMINI_API_KEY:
    gemini_client.configure(GEMINI_API_KEY)
    log.info("Gemini ready  model=%s", GEMINI_MODEL)
else:
    log.warning("GEMINI_API_KEY not set — AI features disabled.")

# ── Mode config ────────────────────────────────────────────────────────────────
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

    Request:  { "messages": [{"role": "user"|"assistant", "text": "..."}], "mode": "..." }
    Response: { "content": "...", "content_devanagari": "...", "script": "...", "mode": "..." }
    """
    if not GEMINI_API_KEY:
        return _error("Chat service not configured. Set GEMINI_API_KEY in backend/.env.", 503)

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
    is_nepal_bhasa = mode_id in NEPAL_BHASA_MODES

    # ── Step 0: Translate user input Nepal Bhasa → Nepali ─────────────────────
    # Only for Nepal Bhasa modes. The history messages have already been stored
    # as Nepali (content_devanagari field), so only translate the latest message.
    messages_for_gemini = list(messages)
    if is_nepal_bhasa:
        raw_user_text = messages[-1]["text"]
        try:
            nepali_user_text = gemini_client.translate_to_nepali(raw_user_text, GEMINI_TRANSLATE_MODEL)
            log.info("[%s] User input → Nepali: %s", mode_id, nepali_user_text[:100])
            # Replace last message with the Nepali translation for Gemini
            messages_for_gemini = list(messages[:-1]) + [
                {"role": "user", "text": nepali_user_text}
            ]
        except Exception as e:
            log.warning("[%s] Input translation failed (%s), sending original", mode_id, e)
            # Fallback: send original text — Gemini will still try to understand it

    # ── Step 1: Gemini → Nepali reply ─────────────────────────────────────────
    try:
        nepali_reply = gemini_client.generate_reply(
            messages=messages_for_gemini,
            model_name=GEMINI_MODEL,
        )
        log.info("[%s] Gemini (Nepali): %s", mode_id, nepali_reply[:100])
    except ValueError as e:
        return _error(str(e), 400)
    except Exception as e:
        log.exception("Gemini error")
        return _error(f"AI service error: {e}", 502)

    # ── Step 2: Translate Gemini reply Nepali → Nepal Bhasa ───────────────────
    devanagari_text = nepali_reply
    if is_nepal_bhasa:
        try:
            nb_text = gemini_client.translate_to_nepal_bhasa(nepali_reply, GEMINI_TRANSLATE_MODEL)
            if nb_text and nb_text.strip():
                devanagari_text = nb_text
                log.info("[%s] Reply → Nepal Bhasa: %s", mode_id, devanagari_text[:100])
            else:
                log.warning("[%s] Nepal Bhasa translation empty, keeping Nepali", mode_id)
        except Exception as e:
            log.warning("[%s] Nepal Bhasa translation failed (%s), keeping Nepali", mode_id, e)

    # ── Step 3: Ranjana — font renders Devanagari visually as Lantsa ──────────
    # NithyaRanjanaDU font uses Devanagari codepoints, no text conversion needed.
    display_text = devanagari_text
    if target_script == "ranjana":
        log.info("[%s] Ranjana font-render: %s", mode_id, display_text[:60])

    return jsonify({
        "content":            display_text,
        "content_devanagari": devanagari_text,   # stored as Nepali in history
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
    """Standalone translation: Nepal Bhasa ↔ Nepali via Gemini."""
    body = request.get_json(silent=True)
    if not body:
        return _error("Request body must be JSON.")
    text      = body.get("text", "")
    direction = body.get("direction", "")   # "to_nepali" or "to_nepal_bhasa"
    if not text:
        return _error("'text' is required.")
    if direction not in ("to_nepali", "to_nepal_bhasa"):
        return _error("'direction' must be 'to_nepali' or 'to_nepal_bhasa'.")
    if not GEMINI_API_KEY:
        return _error("Translation service not configured.", 503)

    if direction == "to_nepali":
        result = gemini_client.translate_to_nepali(text, GEMINI_TRANSLATE_MODEL)
    else:
        result = gemini_client.translate_to_nepal_bhasa(text, GEMINI_TRANSLATE_MODEL)

    return jsonify({"result": result, "direction": direction}), 200


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
