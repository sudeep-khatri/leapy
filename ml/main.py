import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Import your existing modules
from predict import predict_single_image
from transliteration import transliterate
from summarizer import analyze_manuscript

app = FastAPI(
    title="Manuscript Digitization & Analysis API",
    description="API for processing historical Prachalit script manuscripts via CRNN OCR, rule-based transliteration, and Gemini AI.",
    version="1.0.0"
)

# Enable CORS so your future React frontend can talk to this backend smoothly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Temporary folder to store uploaded images for OCR processing
UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
def health_check():
    return {"status": "online", "message": "Manuscript Digitization API is running successfully!"}

@app.post("/api/digitize")
async def digitize_manuscript(file: UploadFile = File(...)):
    """
    Upload a manuscript image. 
    Returns raw OCR, Devanagari conversion, and Gemini historical analysis.
    """
    # Validate file extension
    if not file.filename.lower().endswith((".png", ".jpg", ".jpeg")):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PNG, JPG, and JPEG are supported.")

    # Save uploaded file locally temporarily
    temp_file_path = os.path.join(UPLOAD_DIR, file.filename)
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 1. Run OCR prediction
        raw_prachalit = predict_single_image(temp_file_path)
        if not raw_prachalit:
            raise HTTPException(status_code=500, detail="OCR model failed to extract text from the image.")

        # 2. Transliterate to Devanagari
        devanagari_text = transliterate(raw_prachalit)

        # 3. Analyze with Gemini
        try:
            analysis_result = analyze_manuscript(devanagari_text)
        except Exception as e:
            analysis_result = f"LLM Analysis Warning: Could not reach Gemini API ({str(e)})"

        return {
            "filename": file.filename,
            "raw_ocr": raw_prachalit,
            "devanagari": devanagari_text,
            "analysis": analysis_result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")
        
    finally:
        # Clean up temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)