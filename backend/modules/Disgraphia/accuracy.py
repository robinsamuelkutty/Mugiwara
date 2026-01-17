"""
accuracy.py
Role: Compare OCR-extracted text with expected sentence (from frontend)
Returns: copy accuracy metrics (missing chars, extra chars, accuracy %)

This is a SECONDARY signal. Primary signals are structural handwriting features.
"""

from difflib import SequenceMatcher
from typing import Dict, Tuple


def calculate_copy_accuracy(expected_text: str, extracted_text: str) -> Dict:
    """
    Compare expected sentence with OCR-extracted text.
    Input:
      - expected_text: original sentence from frontend (what user should copy)
      - extracted_text: text recognized from handwriting image
    Output:
      - accuracy metrics
    """
    
    # Normalize texts
    expected = expected_text.lower().strip()
    extracted = extracted_text.lower().strip()
    
    # Character-level accuracy
    total_chars_expected = len(expected)
    
    if total_chars_expected == 0:
        return {
            "copy_accuracy": 0.0,
            "missing_count": 0,
            "extra_count": 0,
            "wrong_count": 0,
            "word_accuracy": 0.0,
            "extraction_confidence": 0.0
        }
    
    # Use SequenceMatcher to find matching/non-matching characters
    matcher = SequenceMatcher(None, expected, extracted)
    matching_chars = sum(block.size for block in matcher.get_matching_blocks())
    
    char_accuracy = matching_chars / total_chars_expected
    
    # Word-level accuracy
    expected_words = expected.split()
    extracted_words = extracted.split()
    
    word_matcher = SequenceMatcher(None, expected_words, extracted_words)
    matching_words = sum(block.size for block in word_matcher.get_matching_blocks())
    total_words = len(expected_words)
    
    word_accuracy = matching_words / total_words if total_words > 0 else 0.0
    
    # Count missing/extra characters
    missing_count = max(0, len(expected) - len(extracted))
    extra_count = max(0, len(extracted) - len(expected))
    
    # Extraction confidence (proxy: how much text was recovered)
    extraction_confidence = min(1.0, len(extracted) / max(1, len(expected)))
    
    return {
        "copy_accuracy": float(char_accuracy),
        "word_accuracy": float(word_accuracy),
        "missing_count": int(missing_count),
        "extra_count": int(extra_count),
        "extraction_confidence": float(extraction_confidence),
        "expected_text": expected_text,
        "extracted_text": extracted_text
    }


def get_accuracy_features(copy_accuracy_dict: Dict) -> Dict:
    """
    Convert raw accuracy metrics into ML feature vector.
    Input: output from calculate_copy_accuracy()
    Output: normalized features for classifier
    """
    
    return {
        "copy_accuracy_score": copy_accuracy_dict.get("copy_accuracy", 0.0),
        "word_accuracy_score": copy_accuracy_dict.get("word_accuracy", 0.0),
        "missing_char_ratio": copy_accuracy_dict.get("missing_count", 0) / max(1, len(copy_accuracy_dict.get("expected_text", ""))),
        "extra_char_ratio": copy_accuracy_dict.get("extra_count", 0) / max(1, len(copy_accuracy_dict.get("expected_text", ""))),
        "extraction_confidence": copy_accuracy_dict.get("extraction_confidence", 0.0)
    }