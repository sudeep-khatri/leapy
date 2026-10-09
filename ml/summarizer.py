import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import errors

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY") or os.getenv("GEMMA_API_KEY"))

def analyze_manuscript(devanagari_text: str) -> str:
    """Takes transliterated Devanagari text from historical manuscripts,
    sends it to the Gemini API, and returns a concise, direct dual-language summary.
    """
    if not devanagari_text or not devanagari_text.strip():
        return "Error: Provided text is empty."

    prompt = f"""
    You are an expert in historical manuscripts, classical Nepali, and Devanagari texts.

    Analyze the following manuscript text and provide accurate, concise information in both English and Nepali. Do not invent missing information. If the text is unclear or cannot be reliably interpreted, state that explicitly.

    Manuscript Text:
    {devanagari_text}

    Follow this exact output format:

    1. Translation / अनुवाद

    English:
    [Direct English translation]

    नेपाली:
    [सटीक नेपाली अनुवाद]

    2. Summary / सारांश

    English:
    [A concise summary in 1–2 sentences]

    नेपाली:
    [१–२ वाक्यमा संक्षिप्त सारांश]

    3. Key Terms / मुख्य शब्दहरू

    * [Term] — [English meaning] | [नेपाली अर्थ]
    * [Term] — [English meaning] | [नेपाली अर्थ]

    Formatting rules:

    * Use plain text headings without asterisks or Markdown symbols.
    * Keep the output clean, professional, and easy to read.
    * Use clear separation between sections.
    * Do not add introductions, conclusions, disclaimers, or unnecessary explanations.
    * Do not fabricate translations, historical facts, or meanings.
    * If a reliable translation is not possible, clearly state the limitation in both languages.
    * Include only key terms relevant to the manuscript.
    """


    models_to_try = ["gemini-3.8-flash", "gemini-2.5-flash"]

    for model_name in models_to_try:
        for attempt in range(1, 3):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                return response.text
            except (errors.ServerError, errors.ClientError):
                time.sleep(1)

    return "Error: Unable to reach the LLM API service after multiple attempts."

if __name__ == "__main__":
    sample_text = "चामातजुछिस्लश्वतियातपाचामातजुछिपञ्चपचारपुजा"

    print("--- Sending Devanagari text to Gemini API ---")
    summary = analyze_manuscript(sample_text)
    print("\n" + "=" * 50)
    print(" SUMMARY RESULT:")
    print("=" * 50)
    print(summary)