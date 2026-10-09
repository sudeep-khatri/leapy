"""
translator.py
-------------
Handles language translation using Google Translate (via deep-translator).

Nepal Bhasa (Newari) has ISO code 'new'. Google Translate supports it
partially — it can detect and translate to/from Nepali ('ne') well, and
has limited Nepal Bhasa support. The strategy here:

1. For Nepal Bhasa modes: we ask Gemini directly in Nepal Bhasa. If the
   user types in Devanagari and we need to ensure the input is in Nepal
   Bhasa (not Nepali), we can optionally detect and translate.
2. For Nepali modes: straightforward — Gemini handles Nepali well natively.
3. This module provides translation utilities that the chat handler calls
   when needed (e.g. translating a Nepali AI reply into Nepal Bhasa).

Google Translate language codes used:
- 'ne'  → Nepali
- 'new' → Newari / Nepal Bhasa (support is limited but present)
- 'en'  → English (fallback)
"""

import warnings
from deep_translator import GoogleTranslator


def translate(text: str, source: str, target: str) -> str:
    """
    Translate text between languages.

    Args:
        text:   Text to translate.
        source: Source language code ('ne', 'new', 'auto').
        target: Target language code ('ne', 'new').

    Returns:
        Translated text, or original on failure.
    """
    if not text or not text.strip():
        return text
    if source == target:
        return text
    try:
        translator = GoogleTranslator(source=source, target=target)
        result = translator.translate(text)
        return result or text
    except Exception as exc:
        warnings.warn(f"Translation failed ({source}→{target}): {exc}")
        return text


def nepali_to_nepal_bhasa(text: str) -> str:
    """Translate Nepali to Nepal Bhasa (Newari) via Google Translate."""
    return translate(text, source="ne", target="new")


def nepal_bhasa_to_nepali(text: str) -> str:
    """Translate Nepal Bhasa to Nepali via Google Translate."""
    return translate(text, source="new", target="ne")


def detect_and_translate_to_nepal_bhasa(text: str) -> str:
    """
    Auto-detect the input language and translate to Nepal Bhasa if it
    looks like Nepali (to help users who typed Nepali by mistake).
    """
    return translate(text, source="auto", target="new")
