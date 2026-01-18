from __future__ import annotations
from typing import TypedDict, Dict, Any, Optional, List


class DyslexiaGraphState(TypedDict, total=False):
    # identity
    user_id: Optional[str]

    # current test level
    current_level: int

    # current level input
    target_text: str
    transcribed_text: str
    word_timestamps: List[Dict[str, Any]]

    # per-level results
    level_scores: Dict[int, float]
    level_results: Dict[int, Dict[str, Any]]

    # routing
    status: str  # IN_PROGRESS | PASS | RETEST | COMPLETED
    next_level: Optional[int]
    should_continue: bool
    message: str

    # final output
    final_result: Optional[str]  # NORMAL | RISK_DYSLEXIA | INCONCLUSIVE

    # meta
    features: Dict[str, Any]
    logs: List[str]