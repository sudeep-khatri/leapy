"""
gemini_client.py  —  Google Gemini wrapper
-------------------------------------------
Always generates Nepali (Devanagari). Language/script conversion downstream.
Retries once on 503 (model overloaded) before giving up.
"""

import time
import logging
from google import genai
from google.genai import types
from google.genai.errors import ServerError

log = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
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


def generate_reply(messages: list[dict], model_name: str = "models/gemini-3.5-flash") -> str:
    """
    Call Gemini and return a Nepali Devanagari reply.
    Retries once after 3 seconds on 503 overload errors.
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
        system_instruction=_SYSTEM_PROMPT,
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
