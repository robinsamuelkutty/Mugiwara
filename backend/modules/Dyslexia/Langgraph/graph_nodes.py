from __future__ import annotations
from typing import Dict, Any
from modules.Disgraphia.preprocessor import preprocess_for_ocr
from modules.Disgraphia.segmentation import extract_segmentation_features
from modules.Disgraphia.features import extract_all_handwriting_features
from modules.Disgraphia.ocr import extract_text, prepare_image_for_clip
from modules.Disgraphia.accuracy import calculate_copy_accuracy, get_accuracy_features
from modules.Disgraphia.clip_similarity import compute_clip_similarity
from modules.Disgraphia.scoring import generate_report
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


def node_compare_and_score(state: DyslexiaGraphState) -> DyslexiaGraphState:
    level = state.current_level

    data = {
        "target_text": state.target_text,
        "transcribed_text": state.transcribed_text,
        "word_timestamps": state.word_timestamps,
    }

    result = compare_text(data)
    word_status = result.get("word_status", [])
    total = len(word_status)

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

    # init
    if state.level_scores is None:
        state.level_scores = {}
    if state.level_results is None:
        state.level_results = {}
    if state.features is None:
        state.features = {}
    if state.logs is None:
        state.logs = []

    state.level_scores[level] = accuracy

    negative_errors = extract_negative_errors(word_status)

    state.level_results[level] = {
        "target_text": state.target_text,
        "transcribed_text": state.transcribed_text,
        "accuracy": accuracy,
        "distance": result.get("distance"),
        "word_status": word_status,
        "negative_errors": negative_errors,
    }

    state.logs.append(f"Level {level} scored: {accuracy}%")
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

def node_dysgraphia_preprocess(state: Dict[str, Any]) -> Dict[str, Any]:
    state.setdefault("logs", [])
    state.setdefault("dysgraphia_features", {})
    state.setdefault("dysgraphia_segmentation", {})
    state.setdefault("dysgraphia_accuracy", {})
    state.setdefault("dysgraphia_report", {})

    if not state.get("dysgraphia_image_bytes"):
        state["dysgraphia_final_result"] = "INCONCLUSIVE"
        state["logs"].append("Dysgraphia skipped: image_bytes missing.")
        return state

    binary = preprocess_for_ocr(state["dysgraphia_image_bytes"])
    state["dysgraphia_binary_image"] = binary
    state["logs"].append("Dysgraphia preprocessing complete.")
    return state


def node_dysgraphia_segmentation(state: Dict[str, Any]) -> Dict[str, Any]:
    seg = extract_segmentation_features(state["dysgraphia_binary_image"])
    state["dysgraphia_segmentation"] = seg
    state["logs"].append("Dysgraphia segmentation complete.")
    return state


def node_dysgraphia_features(state: Dict[str, Any]) -> Dict[str, Any]:
    feats = extract_all_handwriting_features(
        state["dysgraphia_binary_image"],
        state["dysgraphia_segmentation"]
    )
    state["dysgraphia_features"] = feats
    state["logs"].append("Dysgraphia handwriting features extracted.")
    return state


def node_dysgraphia_ocr(state: Dict[str, Any]) -> Dict[str, Any]:
    text = extract_text(state["dysgraphia_binary_image"])
    state["dysgraphia_extracted_text"] = text
    state["logs"].append("Dysgraphia OCR extraction complete.")
    return state


def node_dysgraphia_accuracy(state: Dict[str, Any]) -> Dict[str, Any]:
    expected = state.get("dysgraphia_expected_text", "")
    extracted = state.get("dysgraphia_extracted_text", "")

    acc = calculate_copy_accuracy(expected, extracted)
    acc_feats = get_accuracy_features(acc)

    state["dysgraphia_accuracy"] = acc

    # merge accuracy features into handwriting features dict
    state.setdefault("dysgraphia_features", {})
    state["dysgraphia_features"].update(acc_feats)

    state["logs"].append("Dysgraphia copy accuracy computed.")
    return state


def node_dysgraphia_clip(state: Dict[str, Any]) -> Dict[str, Any]:
    expected = state.get("dysgraphia_expected_text", "")

    img_pil = prepare_image_for_clip(state["dysgraphia_binary_image"])
    sim = compute_clip_similarity(img_pil, expected)

    state["dysgraphia_clip_similarity"] = float(sim)
    state.setdefault("dysgraphia_features", {})
    state["dysgraphia_features"]["clip_similarity_score"] = float(sim)

    state["logs"].append(f"Dysgraphia CLIP similarity computed: {sim:.4f}")
    return state


def node_dysgraphia_scoring(state: Dict[str, Any]) -> Dict[str, Any]:
    report = generate_report(
        features=state.get("dysgraphia_features", {}),
        accuracy=state.get("dysgraphia_accuracy", {}),
        age=state.get("age", 8)
    )

    state["dysgraphia_report"] = report

    risk_level = report.get("risk_level", "Moderate")

    if risk_level == "Low":
        state["dysgraphia_final_result"] = "NORMAL"
    elif risk_level == "High":
        state["dysgraphia_final_result"] = "RISK_DYSGRAPHIA"
    else:
        state["dysgraphia_final_result"] = "INCONCLUSIVE"

    state["logs"].append(f"Dysgraphia final result: {state['dysgraphia_final_result']}")
    return state

