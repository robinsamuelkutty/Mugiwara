import sys
import os
import shutil
import json
import base64
import logging
import sys
import os

# 1. Get the path to 'Dyslexia' (current folder)
current_dir = os.path.dirname(os.path.abspath(__file__))

# 2. Get the path to 'backend' (Two levels up: Dyslexia -> modules -> backend)
backend_dir = os.path.abspath(os.path.join(current_dir, '../../'))

# 3. Add 'backend' to sys.path so Python can find 'modules'
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

# Now this import will work because Python can see the 'modules' folder inside 'backend'
from modules.Disgraphia.vit_features import extract_vit_embedding, vit_structure_score
import numpy as np
import cv2  # Requires: pip install opencv-python-headless
from pathlib import Path
from typing import List, Optional, Dict, Any

# --- PATH FIX: Add Backend root to path ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from fastapi import FastAPI, Query, UploadFile, Form, HTTPException, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# --- GOOGLE GENAI IMPORTS ---
from google import genai
from google.genai import types

# ==========================================
# 1. GLOBAL INITIALIZATION (CRITICAL FIX)
# ==========================================

# A. Setup Logging FIRST so it is always defined
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# B. Load Environment Variables
load_dotenv() 
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# C. Initialize Client Globally
client = None
if not GEMINI_API_KEY:
    logger.error("❌ CRITICAL: GEMINI_API_KEY is missing from environment variables!")
else:
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        logger.info("✅ Gemini Client Initialized Successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Gemini Client: {e}")

# ==========================================
# 2. LOCAL IMPORTS (Safe Block)
# ==========================================
try:
    from rhyme import generate_rhyming_set
    from ran import generate_ran_grid
    from whisper_service import transcribe_with_timestamps
    from story import generate_dyslexia_story
    from compare import compare_text
    from nonsense import nonesense_generator
    
    # Dysgraphia Modules
    from modules.Disgraphia.preprocessor import preprocess_for_ocr
    from modules.Disgraphia.ocr import extract_text, prepare_image_for_clip
    from modules.Disgraphia.segmentation import extract_segmentation_features
    from modules.Disgraphia.features import extract_all_handwriting_features
    from modules.Disgraphia.accuracy import calculate_copy_accuracy
    from modules.Disgraphia.scoring import generate_report
    from modules.Disgraphia.clip_similarity import compute_clip_similarity

    # Dyscalculia Modules
    # IMPORTANT: We import 'get_dyscalculia_prompt' not 'get_dyscalculia_inducing_letters' 
    # to avoid network loops. Ensure your symbol_generator.py matches the previous fix.
    from modules.Dyscalculia.symbol_generator import get_dyscalculia_prompt
    from modules.Dyscalculia.question import fetch_questions

    # Dyslexia Workflow
    from modules.Dyslexia.workflow import run_full_dyslexia_workflow, run_dyslexia_workflow
    from modules.Dyslexia.schemas import (
        DyslexiaRunRequest, 
        DyslexiaRunResponse, 
        DyslexiaLevelRequest, 
        DyslexiaFullEvaluateRequest
    )
    # LangGraph
    from modules.Dyslexia.Langgraph.graph_builder import build_dyslexia_graph

except ImportError as e:
    logger.warning(f"⚠️ Import Warning: {e}. Ensure you are running from the correct directory.")


# ==========================================
# 3. APP SETUP
# ==========================================
app = FastAPI(title="NeuroDiverse Screening API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Common Data Models ---
class QueryRequest(BaseModel):
    prompt: str
    max_new_tokens: int = 300

class WordTimestamp(BaseModel):
    word: str
    start: float
    end: float

class DyslexiaCompareRequest(BaseModel):
    target_text: str
    transcribed_text: str
    word_timestamps: List[WordTimestamp]

# ==========================================
# 4. ENDPOINTS
# ==========================================

@app.get("/")
def home():
    return {"status": "FastAPI is running", "ai_engine": "Gemini"}

@app.post("/generate")
def generate(req: QueryRequest):
    """
    Centralized GenAI endpoint.
    """
    if not client:
        raise HTTPException(status_code=500, detail="Gemini API Key not configured.")

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=req.prompt
        )
        generated_text = response.text if response.text else ""
        return {"response": generated_text}

    except Exception as e:
        logger.error(f"Gemini Generation Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- DYSLEXIA MODULES ---

@app.post("/analyze-audio")
async def analyze_audio(audio_file: UploadFile, target_text: str = Form(...)):
    raw_path = f"temp_{audio_file.filename}"
    try:
        with open(raw_path, "wb") as f:
            shutil.copyfileobj(audio_file.file, f)
        transcription = transcribe_with_timestamps(raw_path)
        return {
            "target_text": target_text,
            "transcribed_text": transcription["transcribed_text"],
            "word_timestamps": transcription["word_timestamps"]
        }
    finally:
        if os.path.exists(raw_path):
            os.remove(raw_path)

@app.get("/dyslexia/story")
def dyslexia_story(difficulty: str = "medium"):
    return generate_dyslexia_story(difficulty=difficulty)

@app.post("/dyslexia/compare")
def dyslexia_compare(data: DyslexiaCompareRequest):
    return compare_text(data.model_dump())

@app.get("/dyslexia/rhymes")
def get_rhymes(level: str = "easy"):
    return {"rhymes": generate_rhyming_set(level)}

@app.get("/dyslexia/ran")
def get_ran_test():
    return generate_ran_grid()

@app.get("/dyslexia/nonsense")
def get_nonsense_words():
    return nonesense_generator()

@app.post("/dyslexia/run-test", response_model=DyslexiaRunResponse)
def run_test_endpoint(payload: DyslexiaRunRequest):
    return run_dyslexia_workflow(payload)

@app.post("/dyslexia/level-evaluate", response_model=DyslexiaRunResponse)
def level_evaluate_endpoint(payload: DyslexiaLevelRequest):
    return run_dyslexia_workflow(payload)

@app.post("/dyslexia/full-evaluate", response_model=DyslexiaRunResponse)
def full_eval_endpoint(payload: DyslexiaFullEvaluateRequest):
    return run_full_dyslexia_workflow(payload)

# LangGraph
graph = build_dyslexia_graph()
@app.post("/dyslexia/langgraph-level")
def run_graph_level(payload: DyslexiaLevelRequest):
    state = {
        "user_id": payload.user_id,
        "current_level": payload.level,
        "target_text": payload.target_text,
        "transcribed_text": payload.transcribed_text,
        "word_timestamps": [wt.model_dump() for wt in payload.word_timestamps],
        "level_scores": {},
        "level_results": {},
        "logs": [],
        "features": {}
    }
    return graph.invoke(state)

# --- DYSCALCULIA MODULES ---

@app.post("/dyscalculia/number_generator")
def generate_number(n: int):
    """
    Generates numbers for Dyscalculia test using Gemini directly.
    """
    try:
        # 1. Check client
        if not client:
             raise HTTPException(status_code=500, detail="Gemini API Key not configured")

        # 2. Get prompt (no network call)
        # Note: If your symbol_generator file still has the old name, update this import
        from modules.Dyscalculia.symbol_generator import get_dyscalculia_prompt
        prompt = get_dyscalculia_prompt(n)
        
        logger.info(f"Generating numbers with prompt length: {len(prompt)}")
        
        # 3. Call Gemini
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt
        )
        
        # 4. Clean result
        result = response.text if response.text else ""
        return result.replace("\n", " ")

    except Exception as e:
        # Logger is definitely defined now
        logger.error(f"❌ Error in number_generator: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def analyze_dyscalculia_image(image: UploadFile) -> str:
    prompt = """
You are analyzing a dyscalculia screening test.

The image contains digits written by a child as part of the screening.
Your task is to judge whether the writing pattern shows signs consistent with dyscalculia.

EVALUATE BASED ON:
- frequent digit reversals or mirroring
- inconsistent number formation
- confusion between similar digits (e.g., 2/5, 6/9, 3/8)
- irregular sequencing or missing digits
- poor number representation that suggests number-symbol difficulty

IMPORTANT:
This is only a screening decision based on this single sample (not a diagnosis).

OUTPUT FORMAT (STRICT):
Return exactly 2 lines:

Line 1: One label only:
LIKELY_DYSCALCULIA
or
UNLIKELY_DYSCALCULIA

Line 2: Reason in 1-2 short sentences, referring only to what is visible in the image.

Do not output anything else.
"""

    img_bytes = await image.read()

    image_part = types.Part.from_bytes(
        data=img_bytes,
        mime_type=image.content_type  # "image/jpeg" or "image/png"
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt, image_part]
    )

    return response.text.strip()


@app.post("/dyscalculia/number_detector")
async def detect_number(image: UploadFile = File(...)):
    result = await analyze_dyscalculia_image(image)

    return {
        "filename": image.filename,
        "result": result
    }

@app.post("/dyscalculia/number_detector")
async def detect_number(image: UploadFile = File(...)):
    result = await analyze_dyscalculia_image(image)

    return {
        "filename": image.filename,
        "result": result
    }


@app.post("/dyscalculia/question_generator")
def generate_question(n:int):
    response = fetch_questions(n)
    return response

#### simple fast api

@app.post("/dyslexia/run-test", response_model=DyslexiaRunResponse)
def run_dyslexia_test(payload: DyslexiaRunRequest):
    try:
        return run_full_dyslexia_workflow(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/dyslexia/level-evaluate", response_model=DyslexiaRunResponse)
def run_dyslexia_test(payload: DyslexiaLevelRequest):
    try:
        return run_full_dyslexia_workflow(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/dyslexia/full-evaluate", response_model=DyslexiaRunResponse)
def full_eval(payload: DyslexiaFullEvaluateRequest):
    try:
        return run_full_dyslexia_workflow(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

MODEL_NAME = "gemini-2.5-flash"
PROMPT = """
You are analyzing a handwritten number image for a dyscalculia screening test.

Step 1: Extract ALL digits/numbers visible in the image (left to right).
Step 2: Identify writing patterns that may indicate difficulty with number formation.

Look for:
- digit reversals (2, 3, 5, 6, 7, 9)
- mirror writing
- digit substitutions (e.g., 6↔9, 1↔7, 3↔8)
- inconsistent spacing or ordering
- unclear or malformed digits

IMPORTANT:
- Do NOT give a medical diagnosis.
- Output only a screening-style risk assessment.

Output ONLY raw JSON (no markdown fences) in this exact format:
{
  "digits": ["..."],
  "complete_number": "...",
  "digit_analysis": [
    {"digit": "...", "confidence": "high/medium/low", "issues": ["reversal/malformed/unclear/none"], "notes": "..."}
  ],
  "observations": ["..."],
  "screening_risk": {
    "risk_level": "LOW" | "MEDIUM" | "HIGH",
    "reason": "short explanation"
  }
}
"""


def parse_gemini_json(response_text: str) -> Dict[str, Any]:
    """Parse JSON from Gemini output safely"""
    text = (response_text or "").strip()

    # remove markdown fences if any
    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()

    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        json_str = text[start:end]
        return json.loads(json_str)
    except Exception:
        return {"raw_response": text}

@app.post("/dyscalculia/problem_detector")
async def number_detector(image: UploadFile = File(...)):
    img_bytes = await image.read()

    if not img_bytes:
        return {"error": "Empty file uploaded"}

    # Use uploaded content-type if possible
    mime_type = image.content_type or "image/jpeg"

    # Gemini request
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[
            PROMPT,
            {
                "inline_data": {
                    "mime_type": mime_type,
                    "data": base64.b64encode(img_bytes).decode("utf-8"),
                }
            },
        ],
    )

    result = parse_gemini_json(response.text)

    return {
        "filename": image.filename,
        "mime_type": mime_type,
        "result": result
    }


### Langgraph

graph = build_dyslexia_graph()

@app.post("/dyslexia/langgraph-level")
def run_graph_level(payload: DyslexiaLevelRequest):
    state = {
        "user_id": payload.user_id,
        "current_level": payload.level,
        "target_text": payload.target_text,
        "transcribed_text": payload.transcribed_text,
        "word_timestamps": [wt.model_dump() for wt in payload.word_timestamps],
        "level_scores": {},      # ⚠️ later we will fix persistence
        "level_results": {},     # ⚠️ later we will fix persistence
        "logs": [],
        "features": {}
    }

    result = graph.invoke(state)
    return result


### Dysgraphia

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
        
        logger.info("Stage 2.75:Vision transformer semantic validation...")
        vit_embedding = extract_vit_embedding(clip_image)
        vit_irregularity = vit_structure_score(vit_embedding)

        logger.info("Stage 3: Segmentation...")
        segmentation_data = extract_segmentation_features(processed_image)

        logger.info("Stage 4: Feature extraction...")
        features = extract_all_handwriting_features(
            processed_image, segmentation_data
        )

        logger.info("Stage 5: Copy accuracy...")
        accuracy = calculate_copy_accuracy(expected_sentence, extracted_text)

        logger.info("Stage 6: Report generation...")
        features["vit_irregularity_score"] = vit_irregularity
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