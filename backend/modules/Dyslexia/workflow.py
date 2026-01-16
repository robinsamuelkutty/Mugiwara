from .schemas import DyslexiaState, DyslexiaFullEvaluateRequest, DyslexiaRunResponse
from .nodes import node_compare_and_score,node_llm_verification

def run_full_dyslexia_workflow(req: DyslexiaFullEvaluateRequest) -> DyslexiaRunResponse:
    state = DyslexiaState(user_id=req.user_id)

    for level in [1, 2, 3, 4]:
        level_data = req.levels.get(level)
        if not level_data:
            continue

        state.current_level = level
        state.target_text = level_data["target_text"]
        state.transcribed_text = level_data["transcribed_text"]
        state.word_timestamps = level_data.get("word_timestamps", [])

        state = node_compare_and_score(state)
    state = node_llm_verification(state)
    # after all levels, final decision will be done by verifier node (next step)
    return DyslexiaRunResponse(
        user_id=state.user_id,
        current_level=4,
        last_accuracy=state.last_accuracy,
        status = state.status,
        final_result = state.final_result,
        next_level=None,
        should_continue=False,
        message=state.message,
        level_scores=state.level_scores,
        features=state.features,
        expected_text="",
        transcribed_text="",
        logs=state.logs
    )
