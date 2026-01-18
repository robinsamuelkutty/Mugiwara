from __future__ import annotations
from typing import Dict, Any

from modules.Dyslexia.compare import compare_text
from modules.Dyslexia.verifier import verify_with_gemini
from modules.Dyslexia.error_reasoner import reason_negative_errors_with_gemini


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


def node_compare_and_score(state: Dict[str, Any]) -> Dict[str, Any]:
    level = state["current_level"]

    data = {
        "target_text": state["target_text"],
        "transcribed_text": state["transcribed_text"],
        "word_timestamps": state.get("word_timestamps", []),
    }

    result = compare_text(data)
    word_status = result.get("word_status", [])
    total = len(word_status)

    # accuracy
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

    # init dicts
    state.setdefault("level_scores", {})
    state.setdefault("level_results", {})
    state.setdefault("features", {})
    state.setdefault("logs", [])

    state["level_scores"][level] = accuracy

    negative_errors = extract_negative_errors(word_status)

    state["level_results"][level] = {
        "target_text": state["target_text"],
        "transcribed_text": state["transcribed_text"],
        "accuracy": accuracy,
        "distance": result.get("distance"),
        "word_status": word_status,
        "negative_errors": negative_errors,
    }

    state["logs"].append(f"Level {level} scored: {accuracy}%")
    return state


def node_decide_route(state: Dict[str, Any]) -> Dict[str, Any]:
    level = state["current_level"]
    acc = state["level_results"][level]["accuracy"]

    state.setdefault("logs", [])
    state.setdefault("features", {})

    # PASS
    if acc >= 40:
        if level < 4:
            state["status"] = "PASS"
            state["next_level"] = level + 1
            state["should_continue"] = True
            state["message"] = f"Passed Level {level}. Go to Level {level+1}."
        else:
            state["status"] = "COMPLETED"
            state["should_continue"] = False
            state["next_level"] = None
            state["message"] = "All levels evaluated. Running final verification."
        state["logs"].append(state["message"])
        return state

    # FAIL (<40)
    # Only Level 1 & 2 can get accent-based retest suggestion
    if level in [1, 2]:
        negative_errors = state["level_results"][level].get("negative_errors", [])
        verdict = reason_negative_errors_with_gemini(level, negative_errors)
        state["features"][f"level_{level}_reasoning"] = verdict

        if verdict.get("suggest_retest") is True and float(verdict.get("confidence", 0.0)) >= 0.6:
            state["status"] = "RETEST"
            state["next_level"] = level
            state["should_continue"] = True
            state["message"] = f"Retest suggested for Level {level}: {verdict.get('reason', '')}"
            state["logs"].append(state["message"])
            return state

    # no retest
    state["status"] = "COMPLETED"
    state["should_continue"] = False
    state["next_level"] = None
    state["message"] = f"Level {level} failed. Proceeding to final verification."
    state["logs"].append(state["message"])
    return state


def node_advance_level(state: Dict[str, Any]) -> Dict[str, Any]:
    # move to next level only if available
    next_level = state.get("next_level")
    if next_level:
        state["current_level"] = next_level
    return state


def node_final_verifier(state: Dict[str, Any]) -> Dict[str, Any]:
    state.setdefault("logs", [])
    state.setdefault("features", {})

    verdict = verify_with_gemini(state.get("level_results", {}))

    llm_result = verdict.get("final_result", "INCONCLUSIVE")
    llm_conf = float(verdict.get("confidence", 0.0))
    llm_reason = verdict.get("reason", "")

    state["features"]["llm_final_result"] = llm_result
    state["features"]["llm_confidence"] = llm_conf
    state["features"]["llm_reason"] = llm_reason

    # safeguard: low confidence -> inconclusive
    if llm_conf < 0.6:
        state["final_result"] = "INCONCLUSIVE"
    else:
        state["final_result"] = llm_result

    state["status"] = "COMPLETED"
    state["should_continue"] = False
    state["next_level"] = None
    state["message"] = f"Final decision: {state['final_result']}"
    state["logs"].append(state["message"])
    return state


def node_error_reasoner(state: Dict[str, Any]) -> Dict[str, Any]:
    level = state["current_level"]

    state.setdefault("logs", [])
    state.setdefault("features", [])

    negative_errors = state["level_results"][level].get("negative_errors", [])
    verdict = reason_negative_errors_with_gemini(level, negative_errors)

    state["features"][f"level_{level}_reasoning"] = verdict

    if verdict.get("suggest_retest") is True and float(verdict.get("confidence", 0.0)) >= 0.6:
        state["status"] = "RETEST"
        state["next_level"] = level
        state["should_continue"] = True
        state["message"] = f"Retest suggested for Level {level}: {verdict.get('reason', '')}"
        state["logs"].append(state["message"])
        return state

    state["status"] = "COMPLETED"
    state["should_continue"] = False
    state["next_level"] = None
    state["message"] = f"Level {level} failed. Proceeding to final verification."
    state["logs"].append(state["message"])
    return state