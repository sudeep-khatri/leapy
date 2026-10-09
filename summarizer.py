import os
import time
from google import genai
from google.genai import errors

API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=API_KEY)


def analyze_manuscript(devanagari_text: str) -> str:
    prompt = f"""
    You are an expert on historical South Asian manuscripts and Nepal Bhasa/Sanskrit texts.
    
    Translate and summarize this transliterated manuscript passage in clear, modern English:
    "{devanagari_text}"
    
    Provide:
    1. Modern English Translation
    2. Key Entities / Terms Mentioned
    3. 1-sentence Executive Summary
    """

    # We try different flash endpoints in case one is congested
    models = ["gemini-2.5-flash", "gemini-3.8-flash"]

    for model_name in models:
        print(f"Trying endpoint: {model_name}...")
        for attempt in range(1, 4):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                return response.text
            except errors.ServerError as e:
                print(
                    f"[{model_name}] Server busy (503). Retrying in 2s... (Attempt {attempt}/3)"
                )
                time.sleep(2)
            except errors.ClientError as e:
                print(f"[{model_name}] Model error: {e}")
                break  # Move to next model

    raise RuntimeError(
        "API server is temporarily busy. Please try again in 1 minute."
    )


if __name__ == "__main__":
    sample_text = "चामातजुछिस्लश्वतियातपाचामातजुछिपञ्चपचारपुजा"

    print("--- Sending Devanagari text to Gemini API ---")
    try:
        summary = analyze_manuscript(sample_text)
        print("\n" + "=" * 50)
        print(" SUMMARY RESULT:")
        print("=" * 50)
        print(summary)
    except Exception as err:
        print(f"\nExecution failed: {err}")