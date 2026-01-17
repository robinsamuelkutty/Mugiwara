from backend.modules.Disgraphia.vit_features import extract_vit_embedding, vit_structure_score
from fastapi import FastAPI, UploadFile, File, HTTPException, Form,Query
from modules.Dyslexia.story import generate_dyslexia_story
from modules.Dyslexia.compare import compare_text
from modules.Dyslexia.rhyme import generate_rhyming_pair
from modules.Dyslexia.nonesense import nonesense_generator
from modules.Dyscalculia.symbol_generator import get_dyscalculia_inducing_digits
from modules.Dyscalculia.question import fetch_questions
from modules.Dyslexia.workflow import run_full_dyslexia_workflow
from modules.Dyslexia.schemas import DyslexiaRunRequest, DyslexiaRunResponse,DyslexiaLevelRequest,DyslexiaFullEvaluateRequest
from modules.Dyslexia.Langgraph.graph import build_dyslexia_langgraph
from modules.Dyscalculia.written_ext_gem import client
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from modules.Disgraphia.story import generate_dysgraphia_story
from pydantic import BaseModel
import logging
from modules.Disgraphia.preprocessor import preprocess_for_ocr
from modules.Disgraphia.ocr import extract_text, prepare_image_for_clip
from modules.Disgraphia.segmentation import extract_segmentation_features
from modules.Disgraphia.features import extract_all_handwriting_features
from modules.Disgraphia.accuracy import calculate_copy_accuracy
from modules.Disgraphia.scoring import generate_report
from modules.Disgraphia.clip_similarity import compute_clip_similarity
from typing import List,Dict,Any
import requests
import cv2
import numpy as np
import json
import base64
from google.genai import types


print("This app is running")

class WordTimestamp(BaseModel):
    word: str
    start: float
    end: float

class DyslexiaCompareRequest(BaseModel):
    target_text: str
    transcribed_text: str
    word_timestamps: List[WordTimestamp]

app = FastAPI()

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

"""
"""
@app.get("/dyslexia/story")
def dyslexia_story(
    difficulty: str = Query("medium", description="easy | medium | hard"),
    age: int = Query(8, ge=3, le=15),
    gender: str | None = Query(None, description="boy | girl | neutral"),
    theme: str | None = Query(None)
):
    return generate_dyslexia_story(difficulty=difficulty)

@app.post("/dyslexia/compare")
def dyslexia_compare(data: DyslexiaCompareRequest):
    result = compare_text(data.model_dump())
    return result

@app.get("/dyslexia/rhyme")
def get_rhyming_pair(level: str = Query("easy", enum=["easy", "medium", "hard"])):
    pair = generate_rhyming_pair(level)

    if not pair:
        raise HTTPException(status_code=500, detail="Failed to generate rhyming pair")

    return {
        "word1": pair[0],
        "word2": pair[1]
    }


@app.get("/dyslexia/nonesense")
def get_nonsense_sentence():
    statement = nonesense_generator()
    return statement.text

## Dyscalculia

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL_NAME = "phi3:mini"

class QueryRequest(BaseModel):
    prompt: str
    max_new_tokens: int = 300

@app.get("/")
def home():
    return {"status": "FastAPI is running", "ollama": "connected"}

@app.post("/generate")
def generate(req: QueryRequest):
    payload = {
        "model": MODEL_NAME,
        "prompt": req.prompt,
        "stream": False,
        "options": {
            "num_predict": req.max_new_tokens
        }
    }

    r = requests.post(OLLAMA_URL, json=payload, timeout=120)
    r.raise_for_status()
    return r.json()

@app.post("/dyscalculia/number_generator")
def generate_number(n:int):
    response = get_dyscalculia_inducing_digits(n)
    clean = response.replace("\n", " ")
    return clean

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
        model=MODEL_NAME,
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

graph = build_dyslexia_langgraph()

@app.post("/dyslexia/langgraph-level")
def run_graph_level(payload: DyslexiaLevelRequest):

    # decode dysgraphia image if provided
    dysgraphia_bytes = None
    if payload.dysgraphia_image_base64:
        try:
            dysgraphia_bytes = base64.b64decode(payload.dysgraphia_image_base64)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid dysgraphia_image_base64")

    state = {
        # dyslexia
        "user_id": payload.user_id,
        "current_level": payload.level,
        "target_text": payload.target_text,
        "transcribed_text": payload.transcribed_text,
        "word_timestamps": [wt.model_dump() for wt in payload.word_timestamps],

        # ✅ persistence (Option A)
        "level_scores": payload.level_scores or {},
        "level_results": payload.level_results or {},

        "logs": [],
        "features": {},

        # dysgraphia (used only after verifier)
        "age": payload.age,
        "dysgraphia_expected_text": payload.dysgraphia_expected_text or "",
        "dysgraphia_image_bytes": dysgraphia_bytes,
    }

    result = graph.invoke(state)
    return result


### Dysgraphia

@app.get("/dysgraphia/story")
def dyslexia_story(
    difficulty: str = Query("medium", description="easy | medium | hard"),
    age: int = Query(8, ge=3, le=15),
    gender: str | None = Query(None, description="boy | girl | neutral"),
    theme: str | None = Query(None)
):
    return generate_dysgraphia_story(difficulty=difficulty)

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

        logger.info("Stage 2.75: vision transformer structure analysis.")
        vit_embedding = extract_vit_embedding(clip_image)
        vit_irregularity_score = vit_structure_score(vit_embedding)

        logger.info("Stage 3: Segmentation...")
        segmentation_data = extract_segmentation_features(processed_image)

        logger.info("Stage 4: Feature extraction...")
        features = extract_all_handwriting_features(
            processed_image, segmentation_data
        )

        logger.info("Stage 5: Copy accuracy...")
        accuracy = calculate_copy_accuracy(expected_sentence, extracted_text)

        logger.info("Stage 6: Report generation...")
        features["vit_structural_irregularity"] = vit_irregularity_score
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
