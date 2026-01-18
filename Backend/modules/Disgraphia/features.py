"""
features.py
Role: Extract handwriting structure features for dysgraphia screening
Receives: segmented lines, words, and binary image
Returns: feature vector (spatial, structural, kinematic approximations)

Key Features (Research-Backed):
  - Letter size variability
  - Baseline drift (vertical inconsistency)
  - Word/letter spacing variance
  - Slant variation
  - Capitalization inconsistency
"""

import numpy as np
from typing import Dict, List
import cv2


def extract_letter_size_features(binary_image, segmentation_data):
    """
    Extract variability in letter sizes across the handwriting.
    Returns: size variance, min size, max size, coefficient of variation
    """
    
    lines = segmentation_data.get("lines", [])
    letter_widths = []
    letter_heights = []
    
    for line in lines:
        words = _segment_words_internal(line["image"])
        for word in words:
            letters = _get_letter_bounds_internal(word["image"])
            for letter_start, letter_end in letters:
                width = letter_end - letter_start + 1
                height = word["image"].shape[0]
                letter_widths.append(width)
                letter_heights.append(height)
    
    if not letter_widths:
        return {
            "letter_width_mean": 0,
            "letter_width_variance": 0,
            "letter_height_mean": 0,
            "letter_height_variance": 0,
            "letter_size_cv": 0  # coefficient of variation
        }
    
    width_mean = np.mean(letter_widths)
    width_var = np.var(letter_widths)
    width_cv = np.std(letter_widths) / width_mean if width_mean > 0 else 0
    
    height_mean = np.mean(letter_heights)
    height_var = np.var(letter_heights)
    
    return {
        "letter_width_mean": float(width_mean),
        "letter_width_variance": float(width_var),
        "letter_height_mean": float(height_mean),
        "letter_height_variance": float(height_var),
        "letter_size_cv": float(width_cv)  # Dysgraphia signature: high CV
    }


def extract_baseline_drift_features(binary_image, segmentation_data):
    """
    Measure vertical alignment consistency (baseline drift).
    Low baseline alignment = dysgraphia indicator.
    Returns: baseline drift variance, regression slope
    """
    
    lines = segmentation_data.get("lines", [])
    
    if not lines:
        return {"baseline_drift": 0, "baseline_regression_slope": 0}
    
    # For each line, find the bottom-most pixel (baseline)
    baselines = []
    
    for line in lines:
        # Horizontal projection from bottom
        h = line["image"].shape[0]
        horizontal_proj = np.sum(line["image"] > 0, axis=1)
        
        # Find bottom baseline (first row from bottom with content)
        for i in range(h - 1, -1, -1):
            if horizontal_proj[i] > 0:
                baselines.append(i)
                break
    
    if len(baselines) < 2:
        return {"baseline_drift": 0, "baseline_regression_slope": 0}
    
    # Variance in baseline positions (drift)
    baseline_drift = np.var(baselines)
    
    # Regression slope: how much baseline shifts across lines
    x = np.arange(len(baselines))
    y = np.array(baselines)
    coeffs = np.polyfit(x, y, 1)
    baseline_slope = coeffs[0]
    
    return {
        "baseline_drift": float(baseline_drift),
        "baseline_regression_slope": float(baseline_slope)
    }


def extract_spacing_features(segmentation_data):
    """
    Extract consistency of word and letter spacing.
    High variance = dysgraphia indicator.
    Returns: spacing variance, inter-letter spacing, inter-word spacing
    """
    
    word_spacings = []
    letter_spacings = []
    
    lines = segmentation_data.get("lines", [])
    
    for line in lines:
        words = _segment_words_internal(line["image"])
        
        # Inter-word spacing
        if len(words) > 1:
            for i in range(len(words) - 1):
                spacing = words[i+1]["bbox"][2] - words[i]["bbox"][3]
                word_spacings.append(spacing)
        
        # Inter-letter spacing
        for word in words:
            letters = _get_letter_bounds_internal(word["image"])
            if len(letters) > 1:
                for i in range(len(letters) - 1):
                    spacing = letters[i+1][0] - letters[i][1]
                    letter_spacings.append(spacing)
    
    word_spacing_var = np.var(word_spacings) if word_spacings else 0
    letter_spacing_var = np.var(letter_spacings) if letter_spacings else 0
    
    word_spacing_mean = np.mean(word_spacings) if word_spacings else 0
    letter_spacing_mean = np.mean(letter_spacings) if letter_spacings else 0
    
    return {
        "word_spacing_variance": float(word_spacing_var),
        "word_spacing_mean": float(word_spacing_mean),
        "letter_spacing_variance": float(letter_spacing_var),
        "letter_spacing_mean": float(letter_spacing_mean),
        "spacing_inconsistency_score": float((word_spacing_var + letter_spacing_var) / 2)
    }


def extract_slant_features(binary_image):
    """
    Measure writing slant (left/right tilt).
    Inconsistent slant = dysgraphia indicator.
    Returns: average slant angle, slant variance across regions
    """
    
    # Divide image into horizontal segments
    num_segments = 5
    h = binary_image.shape[0]
    segment_height = h // num_segments
    
    slant_angles = []
    
    for i in range(num_segments):
        start = i * segment_height
        end = (i + 1) * segment_height if i < num_segments - 1 else h
        
        segment = binary_image[start:end, :]
        coords = np.column_stack(np.where(segment > 0))
        
        if len(coords) < 10:
            continue
        
        # Fit line to pixel coordinates
        try:
            x = coords[:, 1]
            y = coords[:, 0]
            coeffs = np.polyfit(x, y, 1)
            angle = np.arctan(coeffs[0]) * 180 / np.pi
            slant_angles.append(angle)
        except:
            pass
    
    if not slant_angles:
        return {"avg_slant": 0, "slant_variance": 0}
    
    return {
        "avg_slant": float(np.mean(slant_angles)),
        "slant_variance": float(np.var(slant_angles))
    }


def extract_pressure_proxy(binary_image):
    """
    Approximate pen pressure via stroke thickness.
    Inconsistent thickness = dysgraphia indicator.
    Returns: stroke thickness variance
    """
    
    # Erode and dilate to estimate stroke width
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    eroded = cv2.erode(binary_image, kernel, iterations=1)
    
    # Thickness = original - eroded
    thickness_map = cv2.subtract(binary_image, eroded)
    
    # Collect thickness values
    thickness_values = thickness_map[thickness_map > 0]
    
    if len(thickness_values) == 0:
        return {"stroke_thickness_variance": 0, "stroke_thickness_mean": 0}
    
    return {
        "stroke_thickness_mean": float(np.mean(thickness_values)),
        "stroke_thickness_variance": float(np.var(thickness_values))
    }


def extract_all_handwriting_features(binary_image, segmentation_data):
    """
    Extract all structural handwriting features.
    Returns: comprehensive feature dictionary
    """
    
    features = {}
    
    # 1. Size variability
    features.update(extract_letter_size_features(binary_image, segmentation_data))
    
    # 2. Baseline drift
    features.update(extract_baseline_drift_features(binary_image, segmentation_data))
    
    # 3. Spacing consistency
    features.update(extract_spacing_features(segmentation_data))
    
    # 4. Slant variation
    features.update(extract_slant_features(binary_image))
    
    # 5. Pressure/thickness
    features.update(extract_pressure_proxy(binary_image))
    
    # 6. Segmentation metrics (from previous step)
    features.update({
        "num_lines": segmentation_data.get("num_lines", 0),
        "avg_line_height": segmentation_data.get("avg_line_height", 0),
        "total_words": segmentation_data.get("total_words", 0)
    })
    
    return features


# ============ Helper functions ============

def _segment_words_internal(line_image):
    """Internal helper for word segmentation"""
    vertical_projection = np.sum(line_image > 0, axis=0)
    threshold = np.max(vertical_projection) * 0.1 if np.max(vertical_projection) > 0 else 1
    content_cols = np.where(vertical_projection > threshold)[0]
    
    if len(content_cols) == 0:
        return []
    
    words = []
    start = content_cols[0]
    
    for i in range(1, len(content_cols)):
        if content_cols[i] - content_cols[i-1] > 3:
            word_crop = line_image[:, start:content_cols[i-1]+1]
            words.append({"bbox": (0, line_image.shape[0], start, content_cols[i-1]), "image": word_crop})
            start = content_cols[i]
    
    word_crop = line_image[:, start:content_cols[-1]+1]
    words.append({"bbox": (0, line_image.shape[0], start, content_cols[-1]), "image": word_crop})
    
    return words


def _get_letter_bounds_internal(word_image):
    """Internal helper for letter boundary detection"""
    vertical_projection = np.sum(word_image > 0, axis=0)
    threshold = np.max(vertical_projection) * 0.2 if np.max(vertical_projection) > 0 else 1
    content_cols = np.where(vertical_projection > threshold)[0]
    
    if len(content_cols) == 0:
        return []
    
    letter_bounds = []
    start = content_cols[0]
    
    for i in range(1, len(content_cols)):
        if content_cols[i] - content_cols[i-1] > 1:
            letter_bounds.append((start, content_cols[i-1]))
            start = content_cols[i]
    
    letter_bounds.append((start, content_cols[-1]))
    return letter_bounds