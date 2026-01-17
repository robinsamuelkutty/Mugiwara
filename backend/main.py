"""
main.py
Role: FastAPI entry point - orchestrates full screening pipeline
Receives: image file + age + expected sentence
Returns: dysgraphia risk report
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging

from modules.Disgraphia.preprocessor import preprocess_for_ocr
from modules.Disgraphia.ocr import extract_text, prepare_image_for_clip
from modules.Disgraphia.segmentation import extract_segmentation_features
from modules.Disgraphia.features import extract_all_handwriting_features
from modules.Disgraphia.accuracy import calculate_copy_accuracy
from modules.Disgraphia.scoring import generate_report
from modules.Disgraphia.clip_similarity import compute_clip_similarity


# Initialize FastAPI app
app = FastAPI(
    title="Dysgraphia Early Screening System",
    description="AI-powered handwriting analysis for dysgraphia risk screening (ages 5-15)",
    version="0.2.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScreeningRequest(BaseModel):
    age: int
    expected_sentence: str


@app.post("/screen")
async def screening_endpoint(
    file: UploadFile = File(...),
    age: int = Form(...),
    expected_sentence: str = Form(...)
):
    try:
        if age < 5 or age > 15:
            raise ValueError("Age must be between 5 and 15")

        if not expected_sentence.strip():
            raise ValueError("Expected sentence cannot be empty")

        logger.info(f"Processing: age={age}, sentence_len={len(expected_sentence)}")

        file_bytes = await file.read()
        if not file_bytes:
            raise ValueError("Empty file")

        logger.info("Stage 1: Preprocessing image...")
        processed_image = preprocess_for_ocr(file_bytes)

        logger.info("Stage 2: OCR...")
        extracted_text = extract_text(processed_image)

        logger.info("Stage 2.5: CLIP semantic validation...")
        import cv2
        import numpy as np
        raw_np = cv2.imdecode(
            np.frombuffer(file_bytes, np.uint8), cv2.IMREAD_COLOR
        )
        if raw_np is None:
            raise ValueError("Could not decode image for CLIP processing")
        raw_np = cv2.cvtColor(raw_np, cv2.COLOR_BGR2RGB)
        clip_image = prepare_image_for_clip(raw_np)

        clip_similarity = compute_clip_similarity(
            clip_image, expected_sentence )

        # Semantic alignment interpretation (FIXED)
        if clip_similarity < 0.3:
            semantic_alignment = "Low"
        elif clip_similarity < 0.5:
            semantic_alignment = "Moderate"
        else:
            semantic_alignment = "High"

        logger.info("Stage 3: Segmentation...")
        segmentation_data = extract_segmentation_features(processed_image)

        logger.info("Stage 4: Feature extraction...")
        features = extract_all_handwriting_features(
            processed_image, segmentation_data
        )

        logger.info("Stage 5: Copy accuracy...")
        accuracy = calculate_copy_accuracy(expected_sentence, extracted_text)

        logger.info("Stage 6: Report generation...")
        report = generate_report(features, accuracy, age)

        return JSONResponse({
            "success": True,
            "risk_level": report["risk_level"],
            "risk_score": float(report["risk_score"]),
            "age_group": report["age_group"],
            "explanation": report["explanation"],
            "copy_accuracy": accuracy,
            "clip_similarity": round(clip_similarity, 3),
            "semantic_alignment": semantic_alignment,
            "disclaimer": report["disclaimer"],
            "filename": file.filename
        })

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.exception("Unexpected error")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.2.0"}


@app.get("/info")
async def info():
    return {
        "system": "Dysgraphia Early Screening",
        "version": "0.2.0",
        "age_range": "5-15 years"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)