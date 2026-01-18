import uuid
import random
from typing import Dict, Any, List

# --- 🛠 FIX IMPORTS: Use local imports to match app.py structure ---
try:
    from schemas import DyslexiaState, WordTimestamp
    from story import generate_dyslexia_story
    from rhyme import generate_rhyming_set # Updated to 'set' (plural)
    from nonsense import nonesense_generator
    from compare import compare_text
    from whisper_service import transcribe_with_timestamps # Real Whisper
    
    # Assuming these exist, otherwise mock them for now
    try:
        from verifier import verify_with_gemini
        from error_reasoner import reason_negative_errors_with_gemini
    except ImportError:
        # Mocking for now if files missing
        verify_with_gemini = lambda x: {"final_result": "RISK_DYSLEXIA", "confidence": 0.9, "reason": "Mocked verification"}
        reason_negative_errors_with_gemini = lambda l, e: {"suggest_retest": False, "confidence": 0.8, "reason": "Mocked error reasoning"}

except ImportError:
    # Fallback for package runs
    from modules.Dyslexia.schemas import DyslexiaState, WordTimestamp
    from modules.Dyslexia.story import generate_dyslexia_story
    from modules.Dyslexia.rhyme import generate_rhyming_set
    from modules.Dyslexia.nonsense import nonesense_generator
    from modules.Dyslexia.compare import compare_text

# ---------------------------------------------------
# HELPER: Extract Errors
# ---------------------------------------------------
def extract_negative_errors(word_status: list) -> list:
    errors = []
    for w in word_status:
        label = w.get("label", "")
        if label != "correct":
            errors.append({
                "target": w.get("target_word"),
                "spoken": w.get("spoken_word"),
                "label": label,
                "reason": w.get("reason", "")
            })
    return errors

# ---------------------------------------------------
# NODE: Load Input
# ---------------------------------------------------
def node_load_input(state: DyslexiaState, payload: dict) -> DyslexiaState:
    state.user_id = payload.get("user_id")
    state.current_level = payload.get("level", 1)
    state.target_text = payload.get("target_text", "")
    
    # Only load if provided (e.g. testing), usually transcribe fills this
    if "transcribed_text" in payload:
        state.transcribed_text = payload["transcribed_text"]
    if "word_timestamps" in payload:
        state.word_timestamps = payload["word_timestamps"]

    # Initialize results dict if missing
    if state.level_results is None:
        state.level_results = {}
        
    state.logs.append(f"Loaded input for Level {state.current_level}")
    return state

# ---------------------------------------------------
# NODE: Generate Content
# ---------------------------------------------------
def node_generate_content(state: DyslexiaState) -> DyslexiaState:
    level = state.current_level
    
    if level == 1:
        result = generate_dyslexia_story(difficulty="medium")
        state.expected_text = result["story"] if result.get("success") else "The cat sat on the mat."
        state.logs.append(f"Level 1 Generated: {state.expected_text[:30]}...")

    elif level == 2:
        # 🛠 FIX: Using the 'set' function we created earlier
        rhymes = generate_rhyming_set(level="easy")
        if rhymes and len(rhymes) > 0:
             # Take the first pair string "cat hat"
            state.expected_text = rhymes[0] 
        else:
            state.expected_text = "cat hat"
        state.logs.append(f"Level 2 Rhyme: {state.expected_text}")

    elif level == 3:
        # Speed test (RAN) - usually handled by frontend grid, 
        # but here we can set the target text logic
        state.expected_text = "red blue green yellow black" 
        state.logs.append("Level 3 RAN text set")

    elif level == 4:
        # Nonsense
        response = nonesense_generator()
        # Handle if response is dict or text based on your implementation
        text = response.get("words", "") if isinstance(response, dict) else str(response)
        state.expected_text = text
        state.logs.append(f"Level 4 Nonsense: {text}")

    # Sync target_text
    state.target_text = state.expected_text
    return state

# ---------------------------------------------------
# NODE: Transcribe (Real Whisper)
# ---------------------------------------------------
def node_transcribe(state: DyslexiaState) -> DyslexiaState:
    if not state.audio_path:
        state.logs.append("⚠️ Warning: No audio_path provided, skipping transcription.")
        return state

    try:
        # 🛠 FIX: Call real Whisper service
        result = transcribe_with_timestamps(state.audio_path)
        
        state.transcribed_text = result["transcribed_text"]
        # Convert dict timestamps to Pydantic objects if needed, or keep as dicts
        # The schema likely expects a list of dicts or objects
        state.word_timestamps = result["word_timestamps"]
        
        state.logs.append(f"Transcription success: {len(state.transcribed_text)} chars")
    except Exception as e:
        state.logs.append(f"Transcription failed: {str(e)}")
        state.transcribed_text = ""
        state.word_timestamps = []

    return state

# ---------------------------------------------------
# NODE: Compare & Score
# ---------------------------------------------------
def node_compare_and_score(state: DyslexiaState) -> DyslexiaState:
    # 🛠 FIX: Define 'level' FIRST
    level = state.current_level
    
    # 🛠 FIX: Ensure storage exists
    if state.level_results is None:
        state.level_results = {}
        
    data = {
        "target_text": state.target_text,
        "transcribed_text": state.transcribed_text,
        "word_timestamps": state.word_timestamps,
    }

    result = compare_text(data)
    word_status = result.get("word_status", [])
    
    # Extract errors for reasoning
    negative_errors = extract_negative_errors(word_status)

    # 🛠 FIX: Safe assignment now that 'level' and 'level_results' exist
    # Initialize the level dict
    state.level_results[level] = {
        "negative_errors": negative_errors,
        "target_text": state.target_text,
        "transcribed_text": state.transcribed_text,
        "distance": result.get("distance"),
        "word_status": word_status
    }

    # --- Compute Accuracy ---
    total = len(word_status)
    accuracy = 0.0
    
    if total > 0:
        points = 0.0
        for w in word_status:
            label = w.get("label", "")
            if label == "correct":
                points += 1.0
            elif label == "mispronunciation":
                points += 0.5 # Partial credit
        accuracy = (points / total) * 100.0

    accuracy = round(accuracy, 2)

    # Update state
    state.last_accuracy = accuracy
    if state.level_scores is None: 
        state.level_scores = {}
    state.level_scores[level] = accuracy
    
    # Add accuracy to the results dict we created above
    state.level_results[level]["accuracy"] = accuracy

    state.logs.append(f"Level {level} Scored: {accuracy}%")
    return state

# ---------------------------------------------------
# NODE: Decide Next Step (Gatekeeper)
# ---------------------------------------------------
def node_decide_next(state: DyslexiaState) -> DyslexiaState:
    level = state.current_level
    acc = state.last_accuracy

    # Initialize features if needed
    if state.features is None: state.features = {}

    # FAIL CONDITION (< 40%)
    if acc < 40:
        # Check for Retest opportunity in early levels
        if level in [1, 2]:
            negative_errors = state.level_results[level].get("negative_errors", [])
            
            # Ask Gemini why they failed
            verdict = reason_negative_errors_with_gemini(level, negative_errors)
            state.features[f"level_{level}_error_reasoning"] = verdict

            # If Gemini thinks it was just noise or shyness -> RETEST
            if verdict.get("suggest_retest") is True and verdict.get("confidence", 0) >= 0.6:
                state.status = "RETEST"
                state.final_result = None
                state.next_level = level # Stay on current level
                state.should_continue = True
                state.message = f"Retest suggested: {verdict.get('reason')}"
                state.logs.append("DECISION: RETEST")
                return state

        # If not retest -> FAIL/RISK
        state.status = "COMPLETED"
        state.final_result = "RISK_DYSLEXIA"
        state.should_continue = False
        state.next_level = None
        state.message = f"Failed Level {level} ({acc}%). Screening stopped."
        state.logs.append("DECISION: STOP (RISK DETECTED)")
        return state

    # PASS CONDITION
    state.logs.append(f"Passed Level {level}. Checking for next level...")
    if level < 4:
        state.next_level = level + 1
        state.should_continue = True
        state.status = "IN_PROGRESS"
    else:
        state.next_level = None
        state.should_continue = False
        state.status = "VERIFYING" # Go to Final Verification

    return state

# ---------------------------------------------------
# NODE: Final Verification (LLM)
# ---------------------------------------------------
def node_llm_verification(state: DyslexiaState) -> DyslexiaState:
    state.logs.append("Sending all results to Gemini for final profile...")

    if not state.level_results:
        state.final_result = "INCONCLUSIVE"
        state.message = "No data to verify."
        return state

    verdict = verify_with_gemini(state.level_results)

    state.final_result = verdict.get("final_result", "INCONCLUSIVE")
    state.features["llm_confidence"] = verdict.get("confidence", 0.0)
    state.features["llm_reason"] = verdict.get("reason", "")
    
    state.status = "COMPLETED"
    state.message = f"Final Diagnosis: {state.final_result}"
    
    state.logs.append(f"LLM Reason: {state.features['llm_reason']}")
    return state