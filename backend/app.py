from fastapi import APIRouter, Query,FastAPI,HTTPException
from modules.Dyslexia.story import generate_dyslexia_story
from modules.Dyslexia.compare import align_with_timestamps
from modules.Dyslexia.rhyme import generate_rhyming_pair
from pydantic import BaseModel
from typing import List

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

@app.post("/dyslexia/compare")
def dyslexia_compare(
    data: DyslexiaCompareRequest,
    hesitation_threshold: float = 2.0
):
    result = align_with_timestamps(data.model_dump(), hesitation_threshold)
    return result["stats"]

@app.get("/dyslexia/rhyme")
def get_rhyming_pair(level: str = Query("easy", enum=["easy", "medium", "hard"])):
    pair = generate_rhyming_pair(level)

    if not pair:
        raise HTTPException(status_code=500, detail="Failed to generate rhyming pair")

    return {
        "word1": pair[0],
        "word2": pair[1]
    }

