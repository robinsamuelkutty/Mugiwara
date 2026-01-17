from __future__ import annotations
from typing import TypedDict, Dict, Any, Optional, List
from pydantic import BaseModel, Field

class DyslexiaGraphState(BaseModel):
    user_id: Optional[str] = None
    current_level: int = 1

    target_text: str = ""
    transcribed_text: str = ""
    word_timestamps: List[Dict[str, Any]] = Field(default_factory=list)

    level_scores: Dict[int, float] = Field(default_factory=dict)
    level_results: Dict[int, Dict[str, Any]] = Field(default_factory=dict)

    logs: List[str] = Field(default_factory=list)
    features: Dict[str, Any] = Field(default_factory=dict)

    status: str = "IN_PROGRESS"
    next_level: Optional[int] = None
    should_continue: bool = False
    message: str = ""
    final_result: Optional[str] = None

    # ✅ Dysgraphia fields (new)
    age: int = 8
    dysgraphia_expected_text: str = ""
    dysgraphia_image_bytes: Optional[bytes] = None

    dysgraphia_extracted_text: str = ""
    dysgraphia_segmentation: Dict[str, Any] = Field(default_factory=dict)
    dysgraphia_features: Dict[str, Any] = Field(default_factory=dict)
    dysgraphia_accuracy: Dict[str, Any] = Field(default_factory=dict)
    dysgraphia_clip_similarity: float = 0.0
    dysgraphia_report: Dict[str, Any] = Field(default_factory=dict)
    dysgraphia_final_result: Optional[str] = None
