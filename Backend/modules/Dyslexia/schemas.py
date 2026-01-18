# backend/modules/Dyslexia/schemas.py

from __future__ import annotations
import uuid
from typing import Dict, Any, Optional, List, Literal
from pydantic import BaseModel, Field


class WordTimestamp(BaseModel):
    word: str
    start: float
    end: float


class DyslexiaState(BaseModel):
    target_text: str = ""
    retest_suggested: bool = False
    retest_reason: str = ""

    user_id: Optional[str] = None
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    current_level: int = 1
    retest_count: int = 0
    max_retests: int = 2

    audio_path: Optional[str] = None  # ✅ add this

    expected_text: str = ""
    transcribed_text: str = ""
    word_timestamps: List[WordTimestamp] = Field(default_factory=list)

    last_accuracy: float = 0.0
    level_scores: Dict[int, float] = Field(default_factory=dict)
    level_results: Dict[int, Any] = Field(default_factory=dict)
    features: Dict[str, Any] = Field(default_factory=dict)
    status: Literal["IN_PROGRESS", "PASS", "FAIL", "RETEST", "COMPLETED"] = "IN_PROGRESS"
    final_result: Optional[Literal["NORMAL", "RISK_DYSLEXIA", "INCONCLUSIVE"]] = None
    next_level: Optional[int] = None
    should_continue: bool = False
    message: str = ""
    logs: List[str] = Field(default_factory=list)

# ✅ THESE MUST BE OUTSIDE DyslexiaState
class DyslexiaRunRequest(BaseModel):
    user_id: Optional[str] = None
    audio_path: str
    level: int = 1


class DyslexiaRunResponse(BaseModel):
    user_id: Optional[str]
    current_level: int
    last_accuracy: float
    status: str
    final_result: Optional[str]

    next_level: Optional[int] = None          # ✅ new
    should_continue: bool = False             # ✅ new
    message: str = ""                         # ✅ new

    level_scores: Dict[int, float]
    features: Dict[str, Any]
    expected_text: str
    transcribed_text: str
    logs: List[str]

class DyslexiaCompareRequest(BaseModel):
    target_text: str
    transcribed_text: str
    word_timestamps: List[WordTimestamp]
    level: int = 1
    user_id: Optional[str] = None


class DyslexiaLevelRequest(BaseModel):
    user_id: Optional[str] = None
    level: int = 1

    target_text: str
    transcribed_text: str
    word_timestamps: List[WordTimestamp] = Field(default_factory=list)

class DyslexiaFullEvaluateRequest(BaseModel):
    user_id: Optional[str] = None

    # inputs for all 4 levels (each level has its own target+transcribed)
    levels: Dict[int, Dict[str, Any]]