"""
scoring.py
Role: Age-normalize features and classify dysgraphia risk
Receives: feature vectors + age (from frontend)
Returns: risk level (Low/Moderate/High) + explanation

Age ranges: 5-7 (early), 8-10 (middle), 11-15 (late)
"""

import numpy as np
from typing import Dict, Tuple


# Age-based expected ranges (from research and empirical data)
AGE_NORMALIZATION_RULES = {
    "5-7": {
        "letter_size_cv_threshold": 0.35,  # high variance expected at this age
        "baseline_drift_threshold": 15.0,
        "spacing_inconsistency_threshold": 20.0,
        "slant_variance_threshold": 12.0
    },
    "8-10": {
        "letter_size_cv_threshold": 0.25,
        "baseline_drift_threshold": 10.0,
        "spacing_inconsistency_threshold": 15.0,
        "slant_variance_threshold": 8.0
    },
    "11-15": {
        "letter_size_cv_threshold": 0.15,
        "baseline_drift_threshold": 5.0,
        "spacing_inconsistency_threshold": 10.0,
        "slant_variance_threshold": 5.0
    }
}


def get_age_group(age: int) -> str:
    """
    Map age to age group for normalization.
    """
    if 5 <= age <= 7:
        return "5-7"
    elif 8 <= age <= 10:
        return "8-10"
    elif 11 <= age <= 15:
        return "11-15"
    else:
        return "11-15"  # default to oldest group


def normalize_features(features: Dict, age: int) -> Dict:
    """
    Age-normalize handwriting features.
    Converts raw feature values to z-scores within age-appropriate ranges.
    Input:
      - features: output from extract_all_handwriting_features()
      - age: child's age (5-15)
    Output:
      - normalized_features: z-normalized dict
    """
    
    age_group = get_age_group(age)
    thresholds = AGE_NORMALIZATION_RULES[age_group]
    
    normalized = {}
    
    # Normalize each feature by dividing by age-appropriate threshold
    # High normalized value = high dysgraphia risk
    
    normalized["letter_size_cv_norm"] = (
        features.get("letter_size_cv", 0) / max(0.01, thresholds["letter_size_cv_threshold"])
    )
    
    normalized["baseline_drift_norm"] = (
        features.get("baseline_drift", 0) / max(0.01, thresholds["baseline_drift_threshold"])
    )
    
    normalized["spacing_inconsistency_norm"] = (
        features.get("spacing_inconsistency_score", 0) / max(0.01, thresholds["spacing_inconsistency_threshold"])
    )
    
    normalized["slant_variance_norm"] = (
        features.get("slant_variance", 0) / max(0.01, thresholds["slant_variance_threshold"])
    )
    
    # Stroke thickness variance (higher = more pressure inconsistency)
    normalized["stroke_thickness_variance_norm"] = features.get("stroke_thickness_variance", 0)
    
    # Copy accuracy features (lower accuracy = higher risk)
    copy_acc = features.get("copy_accuracy_score", 0.5)
    normalized["copy_accuracy_deviation"] = 1.0 - copy_acc  # 0 = perfect, 1 = terrible

    clip_similarity = features.get("clip_similarity_score", 0.5)
    normalized["visual_semantic_mismatch"] = 1.0 - clip_similarity  # 0 = perfect, 1 = terrible
    
    return normalized


def calculate_risk_score(normalized_features: Dict, age: int) -> Tuple[float, Dict]:
    """
    Calculate weighted dysgraphia risk score (0-1).
    Input: normalized_features from normalize_features()
    Output:
      - risk_score (0-1): 0 = no risk, 1 = high risk
      - component_scores: breakdown by feature
    """
    
    # Weights: spatial structure features are PRIMARY
    weights = {
        "letter_size_cv_norm": 0.22,
        "baseline_drift_norm": 0.18,
        "spacing_inconsistency_norm": 0.22,
       "slant_variance_norm": 0.13,
       "stroke_thickness_variance_norm": 0.10,
       "copy_accuracy_deviation": 0.05,
       "visual_semantic_mismatch": 0.10  # CLIP
    }
    
    component_scores = {}
    weighted_sum = 0.0
    
    for feature, weight in weights.items():
        value = normalized_features.get(feature, 0.0)
        # Sigmoid to cap extreme values
        component_score = min(1.0, max(0.0, value / (1.0 + abs(value))))
        component_scores[feature] = float(component_score)
        weighted_sum += component_score * weight
    
    # Final risk score (0-1)
    risk_score = min(1.0, weighted_sum)
    
    return risk_score, component_scores


def classify_risk_level(risk_score: float, age: int) -> str:
    """
    Classify risk into Low / Moderate / High.
    Thresholds may vary by age.
    """
    
    # Age-adjusted thresholds
    if age <= 7:
        # More lenient for younger children
        if risk_score < 0.35:
            return "Low"
        elif risk_score < 0.65:
            return "Moderate"
        else:
            return "High"
    elif age <= 10:
        # Standard thresholds
        if risk_score < 0.30:
            return "Low"
        elif risk_score < 0.60:
            return "Moderate"
        else:
            return "High"
    else:
        # Stricter for older children
        if risk_score < 0.25:
            return "Low"
        elif risk_score < 0.55:
            return "Moderate"
        else:
            return "High"


def generate_explanation(features: Dict, normalized_features: Dict, component_scores: Dict, age: int) -> Dict:
    """
    Generate human-readable explanation of risk factors.
    Input: raw features, normalized features, component scores
    Output: explanation dict with key contributing factors and recommendations
    """
    
    age_group = get_age_group(age)
    explanation = {
        "age_group": age_group,
        "contributing_factors": [],
        "recommendations": [],
        "strengths": []
    }
    
    # Identify top contributing factors
    sorted_components = sorted(component_scores.items(), key=lambda x: x[1], reverse=True)
    
    for feature_name, score in sorted_components[:3]:
        if score > 0.5:
            explanation["contributing_factors"].append({
                "feature": feature_name,
                "severity": "High" if score > 0.7 else "Moderate",
                "description": _get_feature_description(feature_name)
            })
    
    # Generate recommendations based on top factors
    top_factor = sorted_components[0][0] if sorted_components else None
    
    if top_factor == "letter_size_cv_norm":
        explanation["recommendations"].append("Practice consistent letter sizing")
        explanation["recommendations"].append("Use lined paper with size guides")
    
    if top_factor == "baseline_drift_norm":
        explanation["recommendations"].append("Work on baseline alignment")
        explanation["recommendations"].append("Use multi-lined practice paper")
    
    if top_factor == "spacing_inconsistency_norm":
        explanation["recommendations"].append("Practice regular spacing between letters")
        explanation["recommendations"].append("Use spacing guides or templates")
    
    # Identify strengths
    if component_scores.get("copy_accuracy_deviation", 1.0) < 0.3:
        explanation["strengths"].append("Good copy accuracy - text recognition is working well")
    
    if component_scores.get("letter_size_cv_norm", 0.0) < 0.3:
        explanation["strengths"].append("Consistent letter sizing")
    
    return explanation


def _get_feature_description(feature_name: str) -> str:
    """Map feature names to human-readable descriptions"""
    
    descriptions = {
        "letter_size_cv_norm": "Highly variable letter sizes",
        "baseline_drift_norm": "Inconsistent baseline alignment (letters drift up/down)",
        "spacing_inconsistency_norm": "Inconsistent spacing between letters and words",
        "slant_variance_norm": "Inconsistent slant/tilt of letters",
        "stroke_thickness_variance_norm": "Inconsistent pen pressure or stroke thickness",
        "copy_accuracy_deviation": "Difficulty accurately copying the sentence",
        "visual_semantic_mismatch": "Difficulty visually reproducing the intended sentence"
    }
    
    return descriptions.get(feature_name, feature_name)


def generate_report(
    features: Dict,
    accuracy: Dict,
    age: int
) -> Dict:
    """
    Generate complete dysgraphia screening report.
    Input:
      - features: output from extract_all_handwriting_features()
      - accuracy: output from calculate_copy_accuracy()
      - age: child's age
    Output:
      - comprehensive screening report
    """
    
    # Merge accuracy features into features dict
    features_with_accuracy = features.copy()
    features_with_accuracy["copy_accuracy_score"] = accuracy.get("copy_accuracy", 0.5)
    
    # Normalize
    normalized = normalize_features(features_with_accuracy, age)
    
    # Score
    risk_score, component_scores = calculate_risk_score(normalized, age)
    
    # Classify
    risk_level = classify_risk_level(risk_score, age)
    
    # Explain
    explanation = generate_explanation(
        features_with_accuracy,
        normalized,
        component_scores,
        age
    )

    if normalized.get("visual_semantic_mismatch", 1.0) < 0.3:
        explanation["strengths"].append("Good visual-semantic alignment - handwriting matches intended sentence well")
    
    return {
        "risk_score": float(risk_score),
        "risk_level": risk_level,
        "age_group": get_age_group(age),
        "component_scores": component_scores,
        "explanation": explanation,
        "copy_accuracy_metrics": accuracy,
        "disclaimer": "This is a screening tool, not a diagnostic system. Consult specialists for formal diagnosis.",
        "features_raw": features_with_accuracy
    }