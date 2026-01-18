from schemas import (
    DyslexiaState, 
    DyslexiaFullEvaluateRequest, 
    DyslexiaRunResponse, 
    DyslexiaRunRequest, 
    DyslexiaLevelRequest
)
from nodes import (
    node_compare_and_score, 
    node_llm_verification,
    node_load_input,
    node_generate_content,
    node_transcribe,
    node_decide_next
)

# ---------------------------------------------------
# 1. Full Evaluation (Fixing the 500 Error)
# ---------------------------------------------------
def run_full_dyslexia_workflow(req: DyslexiaFullEvaluateRequest) -> DyslexiaRunResponse:
    state = DyslexiaState(user_id=req.user_id)

    # Convert dictionary input to state format if needed
    levels_dict = req.levels if isinstance(req.levels, dict) else req.levels.dict()

    for level in [1, 2, 3, 4]:
        # Handle string keys or integer keys
        level_data = levels_dict.get(level) or levels_dict.get(str(level))
        if not level_data:
            continue

        state.current_level = level
        state.target_text = level_data.get("target_text", "")
        state.transcribed_text = level_data.get("transcribed_text", "")
        state.word_timestamps = level_data.get("word_timestamps", [])

        # Run scoring node manually
        state = node_compare_and_score(state)

    # Final Verification
    state = node_llm_verification(state)

    # 🛠 FIX: Fill ALL fields required by Pydantic
    return DyslexiaRunResponse(
        user_id=state.user_id,
        level=4,
        status=state.status,
        
        # Pydantic requires these exact names based on your error log:
        current_level=4, 
        last_accuracy=state.last_accuracy if state.last_accuracy else 0.0,
        level_scores=state.level_scores if state.level_scores else {},
        features=state.features if state.features else {},
        expected_text="",  # Not relevant for full report, but required
        transcribed_text="", # Not relevant for full report, but required
        
        final_result=state.final_result,
        message=state.message,
        next_level=None,
        logs=state.logs
    )

# ---------------------------------------------------
# 2. Single Level Run (Fixing the 500 Error)
# ---------------------------------------------------
def run_dyslexia_workflow(req: DyslexiaRunRequest | DyslexiaLevelRequest) -> DyslexiaRunResponse:
    """
    Manually runs the nodes in order: 
    Load -> (Generate) -> (Transcribe) -> Compare -> Decide
    """
    # 1. Initialize State
    state = DyslexiaState(user_id=req.user_id)
    
    # 2. Load Data
    payload = req.model_dump() if hasattr(req, 'model_dump') else req.dict()
    state = node_load_input(state, payload)

    # 3. Determine Flow
    if payload.get("audio_path") or payload.get("transcribed_text"):
        # --- GRADING FLOW ---
        if payload.get("audio_path"):
            state.audio_path = payload["audio_path"]
            state = node_transcribe(state)
        
        state = node_compare_and_score(state)
        state = node_decide_next(state)
    else:
        # --- START FLOW ---
        state = node_generate_content(state)
        state.status = "IN_PROGRESS"
        state.message = "Content generated successfully."

    # 🛠 FIX: Fill ALL fields required by Pydantic
    return DyslexiaRunResponse(
        user_id=state.user_id,
        level=state.current_level,
        status=state.status,
        
        # Pydantic requires these exact names:
        current_level=state.current_level,
        last_accuracy=state.last_accuracy if state.last_accuracy else 0.0,
        level_scores=state.level_scores if state.level_scores else {},
        features=state.features if state.features else {},
        expected_text=state.target_text if state.target_text else "",
        transcribed_text=state.transcribed_text if state.transcribed_text else "",
        
        final_result=state.final_result,
        message=state.message,
        next_level=state.next_level,
        logs=state.logs
    )