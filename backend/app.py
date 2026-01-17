from fastapi import APIRouter, Query,FastAPI,HTTPException
from modules.Dyslexia.story import generate_dyslexia_story
from modules.Dyslexia.compare import compare_text
from modules.Dyslexia.rhyme import generate_rhyming_pair
from modules.Dyslexia.nonesense import nonesense_generator
from modules.Dyscalculia.symbol_generator import get_dyscalculia_inducing_letters
from modules.Dyscalculia.question import fetch_questions
from modules.Dyslexia.workflow import run_full_dyslexia_workflow
from modules.Dyslexia.schemas import DyslexiaRunRequest, DyslexiaRunResponse,DyslexiaLevelRequest,DyslexiaFullEvaluateRequest
from modules.Dyslexia.Langgraph.graph_builder import build_dyslexia_graph
from pydantic import BaseModel
from typing import List
import requests

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

@app.get("/")
def welcome():
    return "Hello World!"

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
    response = get_dyscalculia_inducing_letters(n)
    clean = response.replace("\n", " ")
    return clean


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
