"""
script_converter.py
-------------------
Handles script conversion between Devanagari, Newa (Nepal Bhasa script),
and Ranjana (Lantsa) using the aksharamukha library.

The aksharamukha library is used as a Python package (installed via pip),
not copied from the ZIP. This complies with its GPL-3.0 license because
we are not distributing modified source — we are calling it as a dependency.

Key findings from testing:
- Devanagari → Newa works directly (Newa Unicode block U+11400–U+1147F)
- Devanagari → Ranjana requires post_options=['ranjanalantsa'] — the output
  lands in the Tibetan Unicode range (U+0F00+) which is rendered visually
  as Ranjana/Lantsa by the RanjanaUNICODE font.
- Plain 'Ranjana' target without the post-option returns the source unchanged.
"""

import warnings
from aksharamukha import transliterate


def devanagari_to_newa(text: str) -> str:
    """Convert Devanagari text to Newa script (Nepal Bhasa traditional script)."""
    if not text or not text.strip():
        return text
    try:
        result = transliterate.process(
            "Devanagari",
            "Newa",
            text,
            nativize=True,
            pre_options=[],
            post_options=[],
        )
        return result or text
    except Exception as exc:
        warnings.warn(f"Newa conversion failed: {exc}")
        return text


def devanagari_to_ranjana(text: str) -> str:
    """
    Convert Devanagari text to Ranjana script (Lantsa style).

    The output uses Tibetan Unicode codepoints that are rendered as Ranjana
    glyphs by the RanjanaUNICODE.ttf / Noto Serif Tibetan fonts.
    """
    if not text or not text.strip():
        return text
    try:
        result = transliterate.process(
            "Devanagari",
            "Ranjana",
            text,
            nativize=True,
            pre_options=[],
            post_options=["ranjanalantsa"],
        )
        # If conversion returns empty or identical, fall back to Newa
        if not result or result == text:
            return devanagari_to_newa(text)
        return result
    except Exception as exc:
        warnings.warn(f"Ranjana conversion failed: {exc}")
        # Graceful fallback: return Newa if Ranjana fails
        return devanagari_to_newa(text)


def convert_script(text: str, target_script: str) -> str:
    """
    Public entry point.

    Args:
        text:          Devanagari text to convert.
        target_script: One of 'devanagari', 'newa', 'ranjana'.

    Returns:
        Converted text, or original text on failure.
    """
    if target_script == "devanagari":
        return text
    if target_script == "newa":
        return devanagari_to_newa(text)
    if target_script == "ranjana":
        return devanagari_to_ranjana(text)
    return text

