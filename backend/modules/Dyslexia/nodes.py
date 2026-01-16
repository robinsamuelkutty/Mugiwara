# backend/modules/Dyslexia/nodes.py
import uuid
import random
from typing import Dict, Any
from modules.Dyslexia.schemas import DyslexiaState, WordTimestamp
from modules.Dyslexia.story import generate_dyslexia_story
from modules.Dyslexia.rhyme import generate_rhyming_pair
from modules.Dyslexia.nonesense import nonesense_generator
from modules.Dyslexia.compare import compare_text
from modules.Dyslexia.verifier import verify_with_gemini
from modules.Dyslexia.error_reasoner import reason_negative_errors_with_gemini

# Assume you have a real speech-to-text function (Whisper / Google STT / etc.)
# This is a placeholder — replace with your actual implementation

def node_llm_verification(state: DyslexiaState) -> DyslexiaState:
    state.logs.append("Sending level_results to Gemini for final verification...")

    verdict = verify_with_gemini(state.level_results)

    state.final_result = verdict.get("final_result", "INCONCLUSIVE")
    state.features["llm_confidence"] = verdict.get("confidence", 0.0)
    state.features["llm_reason"] = verdict.get("reason", "")

    state.status = "COMPLETED"
    state.message = f"LLM Verification done: {state.final_result}"

    state.logs.append(state.message)
    state.logs.append(f"LLM Reason: {state.features['llm_reason']}")

    return state

def node_load_input(state: DyslexiaState, payload: dict) -> DyslexiaState:
    """
    Load the request JSON into the state
    """
    state.user_id = payload.get("user_id")
    state.current_level = payload.get("level", 1)

    state.target_text = payload["target_text"]
    state.transcribed_text = payload["transcribed_text"]
    state.word_timestamps = payload.get("word_timestamps", [])

    state.logs.append("Loaded input text + transcript + timestamps into state.")
    return state



def transcribe_audio(audio_path: str) -> tuple[str, list[dict]]:
    """Placeholder: Replace with real STT"""
    # Example fake output
    return "the quick brown fox", [
        {"word": "the", "start": 0.1, "end": 0.4},
        {"word": "quick", "start": 0.5, "end": 0.9},
        # ...
    ]

def node_generate_content(state: DyslexiaState) -> DyslexiaState:
    """Node 1: Generate expected text for current level"""
    level = state.current_level

    if level == 1:
        result = generate_dyslexia_story(difficulty="medium")
        if result["success"]:
            state.expected_text = result["story"]
            state.logs.append(f"Level 1 story generated. Theme: {result['theme']}")
        else:
            state.logs.append("Failed to generate story → using fallback")
            state.expected_text = "The cat sat on the mat."

    elif level == 2:
        pair = generate_rhyming_pair(level="easy")
        if pair:
            word1, word2 = pair
            state.expected_text = f"Say these words: {word1}, {word2}"
            state.logs.append(f"Rhyming pair: {word1} - {word2}")
        else:
            state.expected_text = "cat hat"

    elif level == 3:
        # Speed test → longer story or repeated phrase
        result = generate_dyslexia_story(difficulty="easy", words_count=12, target_sentences=4)
        state.expected_text = result.get("story", "Read this quickly: Hello world test.")
        state.logs.append("Level 3 speed test text generated")

    elif level == 4:
        response = nonesense_generator()
        nonsense = response.text.strip()
        state.expected_text = f"Try to read these made-up words: {nonsense}"
        state.logs.append("Nonsense words generated")

    return state


def node_transcribe(state: DyslexiaState) -> DyslexiaState:
    """Node 2: Transcribe audio"""
    if not state.audio_path:  # we'll set this later
        state.logs.append("Error: No audio_path provided")
        return state

    transcribed, raw_timestamps = transcribe_audio(state.audio_path)

    state.transcribed_text = transcribed
    state.word_timestamps = [WordTimestamp(**ts) for ts in raw_timestamps]
    state.logs.append(f"Transcription completed. Length: {len(transcribed.split())} words")

    return state


def node_compare_and_score(state: DyslexiaState) -> DyslexiaState:
    data = {
        "target_text": state.target_text,
        "transcribed_text": state.transcribed_text,
        "word_timestamps": state.word_timestamps,
    }

    result = compare_text(data)

    word_status = result.get("word_status", [])
    negative_errors = extract_negative_errors(word_status)
    state.level_results[level]["negative_errors"] = negative_errors
    total = len(word_status)

    # --- compute accuracy ---
    if total == 0:
        accuracy = 0.0
    else:
        points = 0.0
        for w in word_status:
            label = w.get("label", "")
            if label == "correct":
                points += 1.0
            elif label == "mispronunciation":
                points += 0.5
        accuracy = (points / total) * 100.0

    accuracy = round(accuracy, 2)

    # --- update current state values ---
    state.last_accuracy = accuracy
    state.level_scores[state.current_level] = accuracy

    # --- store per-level evidence for final LLM decision ---
    level = state.current_level

    # IMPORTANT: ensure this exists in state schema
    if not hasattr(state, "level_results") or state.level_results is None:
        state.level_results = {}

    state.level_results[level] = {
        "target_text": state.target_text,
        "transcribed_text": state.transcribed_text,
        "accuracy": accuracy,
        "distance": result.get("distance"),
        "word_status": word_status
    }

    state.logs.append(f"Stored Level {level} evidence.")
    state.logs.append(f"Comparison complete. Accuracy={accuracy:.2f}%")

    return state



def node_decide_next(state: DyslexiaState) -> DyslexiaState:
    level = state.current_level
    acc = state.last_accuracy

    # FAIL path
    if acc < 40:

        # Only for Level 1 and Level 2
        if level in [1, 2]:
            negative_errors = state.level_results[level].get("negative_errors", [])

            verdict = reason_negative_errors_with_gemini(level, negative_errors)

            state.features[f"level_{level}_error_reasoning"] = verdict

            if verdict.get("suggest_retest") is True and verdict.get("confidence", 0) >= 0.6:
                state.status = "RETEST"
                state.final_result = None
                state.next_level = level
                state.should_continue = True
                state.message = f"Retest suggested for Level {level}: {verdict.get('reason')}"
                state.logs.append(state.message)
                return state

        # If not retest suggested -> normal fail
        state.status = "COMPLETED"
        state.final_result = "RISK_DYSLEXIA"
        state.should_continue = False
        state.next_level = None
        state.message = f"Failed Level {level}. Screening indicates dyslexia risk."
        state.logs.append(state.message)
        return state

def node_llm_verification(state):
    """
    Final verification node:
    Uses Gemini to decide final_result based on state.level_results
    """
    state.logs.append("LLM verification started (Gemini).")

    # Safety: if no evidence, return inconclusive
    if not state.level_results or len(state.level_results) == 0:
        state.final_result = "INCONCLUSIVE"
        state.status = "COMPLETED"
        state.message = "No level evidence found for verification."
        state.logs.append(state.message)
        return state

    verdict = verify_with_gemini(state.level_results)

    state.final_result = verdict.get("final_result", "INCONCLUSIVE")
    state.status = "COMPLETED"

    # Store extra info into features
    if state.features is None:
        state.features = {}

    state.features["llm_confidence"] = verdict.get("confidence", 0.0)
    state.features["llm_reason"] = verdict.get("reason", "")

    state.message = f"Gemini verification completed: {state.final_result}"
    state.logs.append(state.message)
    state.logs.append(f"LLM Reason: {state.features['llm_reason']}")

    return state

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
