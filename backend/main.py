from fastapi import APIRouter, Query,FastAPI
from modules.Dyslexia.story import generate_dyslexia_story

app = FastAPI()

router = APIRouter(prefix="/dyslexia", tags=["Dyslexia"])

@app.get("/dyslexia/story")
def dyslexia_story(
    difficulty: str = Query("medium", description="easy | medium | hard"),
    age: int = Query(8, ge=3, le=15),
    gender: str | None = Query(None, description="boy | girl | neutral"),
    theme: str | None = Query(None)
):
    return generate_dyslexia_story(
        difficulty=difficulty)
