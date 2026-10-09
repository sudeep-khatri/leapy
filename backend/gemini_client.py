"""
gemini_client.py  —  Google Gemini wrapper
-------------------------------------------
Provides two operations:
  1. generate_reply()         — chat reply in Nepali Devanagari
  2. translate_to_nepal_bhasa() — translate Nepali text to Nepal Bhasa
  3. translate_to_nepali()    — translate Nepal Bhasa (or any Devanagari) to Nepali

All Nepal Bhasa translation is done by Gemini because Google Translate does
not support the 'new' (Newari) language code at all.

Retries once on 503 (model overloaded) before giving up.
"""

import time
import logging
from google import genai
from google.genai import types
from google.genai.errors import ServerError

log = logging.getLogger(__name__)

# System prompt for chat: always answer in Nepali
_CHAT_SYSTEM_PROMPT = (
    "You are a helpful, friendly assistant. "
    "Always respond in Nepali language using Devanagari script. "
    "Be concise and natural. Do not switch to English unless the user writes in English."
)

_client: genai.Client | None = None


def configure(api_key: str) -> None:
    global _client
    _client = genai.Client(api_key=api_key)


def _get_client() -> genai.Client:
    if _client is None:
        raise RuntimeError("Gemini client not configured. Call configure() first.")
    return _client


def _call_gemini(prompt: str, model_name: str, system: str | None = None) -> str:
    """Single Gemini call with one retry on 503."""
    client = _get_client()
    config = types.GenerateContentConfig(
        temperature=0.3,
        max_output_tokens=1024,
    )
    if system:
        config = types.GenerateContentConfig(
            system_instruction=system,
            temperature=0.3,
            max_output_tokens=1024,
        )
    for attempt in range(2):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config,
            )
            text = response.text
            if not text or not text.strip():
                raise RuntimeError("Gemini returned an empty response.")
            return text.strip()
        except ServerError as e:
            if "503" in str(e) and attempt == 0:
                log.warning("Gemini 503 overloaded, retrying in 3s...")
                time.sleep(3)
                continue
            raise
    raise RuntimeError("Gemini unavailable after retry.")


def generate_reply(messages: list[dict], model_name: str = "models/gemini-3.5-flash") -> str:
    """
    Send conversation history to Gemini. Returns a Nepali Devanagari reply.
    The messages are already in Nepali (user input was translated before this call).
    """
    if not messages:
        raise ValueError("messages list cannot be empty")

    client = _get_client()
    history: list[types.Content] = []
    for msg in messages[:-1]:
        role = "model" if msg["role"] == "assistant" else "user"
        history.append(types.Content(role=role, parts=[types.Part(text=msg["text"])]))

    user_text = messages[-1]["text"]
    contents = [
        *history,
        types.Content(role="user", parts=[types.Part(text=user_text)]),
    ]
    config = types.GenerateContentConfig(
        system_instruction=_CHAT_SYSTEM_PROMPT,
        temperature=0.7,
        top_p=0.95,
        max_output_tokens=1024,
    )

    for attempt in range(2):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config,
            )
            text = response.text
            if not text or not text.strip():
                raise RuntimeError("Gemini returned an empty response.")
            return text.strip()
        except ServerError as e:
            if "503" in str(e) and attempt == 0:
                log.warning("Gemini 503 overloaded, retrying in 3s...")
                time.sleep(3)
                continue
            raise
    raise RuntimeError("Gemini unavailable after retry.")


def translate_to_nepal_bhasa(nepali_text: str, model_name: str = "models/gemini-flash-lite-latest") -> str:
    """
    Translate Nepali text to Nepal Bhasa (Newari) using Gemini.

    Uses a strict translation prompt so Gemini only outputs the Nepal Bhasa
    translation without any explanation or extra text.
    """
    if not nepali_text or not nepali_text.strip():
        return nepali_text

    prompt = (
        "Translate the following Nepali text to Nepal Bhasa (Newari language, "
        "written in Devanagari script). "
        "Output ONLY the Nepal Bhasa translation — no explanation, no transliteration, "
        "no extra text. Keep the same tone and meaning.\n\n"
        f"Nepali text: {nepali_text}\n\n"
        "Nepal Bhasa translation:"
    )

    try:
        result = _call_gemini(prompt, model_name)
        # Strip any accidental prefix like "Nepal Bhasa translation:" that Gemini might add
        for prefix in ["Nepal Bhasa translation:", "Translation:", "नेपाल भाषा:"]:
            if result.startswith(prefix):
                result = result[len(prefix):].strip()
        return result if result else nepali_text
    except Exception as e:
        log.warning("Nepal Bhasa translation failed: %s", e)
        return nepali_text  # Graceful fallback: return Nepali


def translate_to_nepali(text: str, model_name: str = "models/gemini-flash-lite-latest") -> str:
    """
    Translate Nepal Bhasa (or any Devanagari) input to Nepali using Gemini.
    Used to convert user's Nepal Bhasa message into Nepali before Gemini processes it.
    """
    if not text or not text.strip():
        return text

    prompt = (
        "The following text may be written in Nepal Bhasa (Newari), Nepali, or a mix. "
        "Translate it to standard Nepali (written in Devanagari script). "
        "Output ONLY the Nepali translation — no explanation, no extra text.\n\n"
        f"Input text: {text}\n\n"
        "Nepali translation:"
    )

    try:
        result = _call_gemini(prompt, model_name)
        for prefix in ["Nepali translation:", "Translation:"]:
            if result.startswith(prefix):
                result = result[len(prefix):].strip()
        return result if result else text
    except Exception as e:
        log.warning("Nepal Bhasa → Nepali translation failed: %s", e)
        return text  # Graceful fallback: pass original text to Gemini
