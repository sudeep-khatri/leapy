import os
import pandas as pd
from predict import predict_single_image, resolve_image_path, PROJECT_ROOT
from transliteration import transliterate
from summarizer import analyze_manuscript  # Your Gemini analysis module

def run_full_pipeline(image_path: str):
    """
    End-to-End Pipeline:
    1. Image -> CRNN Model OCR -> Raw Prachalit Text (via predict.py)
    2. Raw Prachalit Text -> Transliteration Map -> Modern Devanagari (via transliterate.py)
    3. Modern Devanagari -> Gemini API -> Bilingual Historical Analysis (via summarizer.py)
    """
    print(f"\n[Pipeline] Step 1: Running OCR inference on image...")
    raw_prachalit = predict_single_image(image_path)
    
    if not raw_prachalit:
        return {"error": "OCR model failed to decode text from the image."}
    print(f"[Pipeline] Raw OCR Output (Prachalit): {raw_prachalit}")

    print(f"[Pipeline] Step 2: Transliterating to Modern Devanagari...")
    devanagari_text = transliterate(raw_prachalit)
    print(f"[Pipeline] Converted Devanagari: {devanagari_text}")

    print(f"[Pipeline] Step 3: Sending to Gemini for philological analysis...")
    analysis_result = analyze_manuscript(devanagari_text)

    return {
        "image_path": image_path,
        "raw_ocr": raw_prachalit,
        "devanagari": devanagari_text,
        "analysis": analysis_result
    }

if __name__ == "__main__":
    print("==================================================")
    print("   MANUSCRIPT DIGITIZATION PIPELINE TEST")
    print("==================================================")
    
    test_csv = os.path.join(PROJECT_ROOT, "data_splits", "test.csv")
    
    if os.path.exists(test_csv):
        df = pd.read_csv(test_csv)
        row = df.sample(n=1).iloc[0]
        
        img_col = "image_path" if "image_path" in df.columns else df.columns[0]
        text_col = "text" if "text" in df.columns else df.columns[1]
        
        raw_filename = row[img_col]
        ground_truth = row[text_col] if text_col in df.columns else "N/A"
        
        image_path = resolve_image_path(os.path.join(PROJECT_ROOT, "images"), raw_filename)
        
        if image_path:
            print(f"Testing with image: {image_path}")
            print(f"Dataset Ground Truth : {ground_truth}")
            
            result = run_full_pipeline(image_path)
            
            print("\n================ FINAL PIPELINE RESULT ================")
            print(f"Devanagari Text : {result['devanagari']}")
            print("\n--- Gemini Analysis ---")
            print(result['analysis'])
            print("=======================================================")
        else:
            print(f"Could not locate image '{raw_filename}' inside 'images/'.")
    else:
        print(f"Test CSV not found at: {test_csv}")