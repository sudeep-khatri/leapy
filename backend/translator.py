"""
translator.py
-------------
Language translation utilities.

Key finding: Google Translate's free endpoint (via deep-translator) does NOT
support Nepal Bhasa ('new') as a source or target language — it raises
LanguageNotSupportedException immediately. Additionally, the free endpoint
is rate-limited at the IP level and unreliable.

Strategy: Use Gemini for all Nepal Bhasa translation. Gemini understands
Nepal Bhasa in context and can translate it reliably. The translate()
function here is kept as a utility for Nepali ↔ Nepali operations only.
"""

import warnings
from deep_translator import GoogleTranslator


def translate_nepali_to_nepali(text: str) -> str:
    """Identity — kept for API compatibility. Nepali stays Nepali."""
    return text


def translate(text: str, source: str, target: str) -> str:
    """
    Translate between supported Google Translate languages.
    NOTE: 'new' (Nepal Bhasa) is NOT supported. Use gemini_client functions instead.
    """
    if not text or not text.strip():
        return text
    if source == target:
        return text
    try:
        result = GoogleTranslator(source=source, target=target).translate(text)
        return result or text
    except Exception as exc:
        warnings.warn(f"Translation failed ({source}→{target}): {exc}")
        return text
