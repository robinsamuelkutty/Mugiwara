"""
segmentation.py
Role: Segment handwriting into lines and words for structural analysis
Receives: preprocessed binary image (numpy array)
Returns: list of line regions, word regions, letter bounding boxes
"""

import cv2
import numpy as np
from typing import List, Tuple


def segment_lines(binary_image):
    """
    Segment image into individual text lines.
    Input: preprocessed binary image
    Output: list of line crops (numpy arrays) with bounding boxes
    """
    
    # Horizontal projection: sum pixels per row
    horizontal_projection = np.sum(binary_image > 0, axis=1)
    
    # Find rows with content (threshold to filter noise)
    threshold = np.max(horizontal_projection) * 0.1
    content_rows = np.where(horizontal_projection > threshold)[0]
    
    if len(content_rows) == 0:
        return []
    
    # Find gaps between lines (consecutive empty rows)
    line_gaps = []
    for i in range(1, len(content_rows)):
        if content_rows[i] - content_rows[i-1] > 2:  # gap larger than 2 pixels
            line_gaps.append((content_rows[i-1], content_rows[i]))
    
    # Extract line bounding boxes
    lines = []
    start = content_rows[0]
    
    for end, next_start in line_gaps:
        line_bbox = (start, end, 0, binary_image.shape[1])
        line_crop = binary_image[start:end+1, :]
        lines.append({
            "bbox": line_bbox,  # (top, bottom, left, right)
            "image": line_crop
        })
        start = next_start
    
    # Last line
    line_bbox = (start, content_rows[-1], 0, binary_image.shape[1])
    line_crop = binary_image[start:content_rows[-1]+1, :]
    lines.append({
        "bbox": line_bbox,
        "image": line_crop
    })
    
    return lines


def segment_words(line_image):
    """
    Segment a single line into words.
    Input: binary image of one line
    Output: list of word crops with bounding boxes
    """
    
    # Vertical projection: sum pixels per column
    vertical_projection = np.sum(line_image > 0, axis=0)
    
    threshold = np.max(vertical_projection) * 0.1
    content_cols = np.where(vertical_projection > threshold)[0]
    
    if len(content_cols) == 0:
        return []
    
    # Find gaps between words (consecutive empty columns)
    word_gaps = []
    for i in range(1, len(content_cols)):
        if content_cols[i] - content_cols[i-1] > 3:  # gap larger than 3 pixels
            word_gaps.append((content_cols[i-1], content_cols[i]))
    
    # Extract word bounding boxes
    words = []
    start = content_cols[0]
    
    for end, next_start in word_gaps:
        word_bbox = (0, line_image.shape[0], start, end)
        word_crop = line_image[:, start:end+1]
        words.append({
            "bbox": word_bbox,
            "image": word_crop
        })
        start = next_start
    
    # Last word
    word_bbox = (0, line_image.shape[0], start, content_cols[-1])
    word_crop = line_image[:, start:content_cols[-1]+1]
    words.append({
        "bbox": word_bbox,
        "image": word_crop
    })
    
    return words


def get_letter_bounds(word_image):
    """
    Approximate individual letter bounding boxes in a word.
    Uses connected components or simple column analysis.
    Input: binary image of one word
    Output: list of letter bounding boxes
    """
    
    # Vertical projection: sum pixels per column
    vertical_projection = np.sum(word_image > 0, axis=0)
    
    threshold = np.max(vertical_projection) * 0.2  # stricter threshold
    content_cols = np.where(vertical_projection > threshold)[0]
    
    if len(content_cols) == 0:
        return []
    
    # Find letter boundaries (small gaps between columns)
    letter_bounds = []
    start = content_cols[0]
    
    for i in range(1, len(content_cols)):
        if content_cols[i] - content_cols[i-1] > 1:
            # End of letter
            letter_bounds.append((start, content_cols[i-1]))
            start = content_cols[i]
    
    # Last letter
    letter_bounds.append((start, content_cols[-1]))
    
    return letter_bounds


def extract_segmentation_features(binary_image):
    """
    Extract segmentation-based features from the entire image.
    Returns: dict with line metrics, word metrics, spacing info
    """
    
    lines = segment_lines(binary_image)
    
    if len(lines) == 0:
        return {
            "num_lines": 0,
            "avg_line_height": 0,
            "line_height_variance": 0,
            "total_words": 0,
            "avg_word_spacing": 0,
            "avg_word_height": 0
        }
    
    # Line-level metrics
    line_heights = [line["bbox"][1] - line["bbox"][0] for line in lines]
    avg_line_height = np.mean(line_heights)
    line_height_variance = np.var(line_heights)
    
    # Word-level metrics
    all_words = []
    word_spacings = []
    
    for line in lines:
        words = segment_words(line["image"])
        all_words.extend(words)
        
        # Inter-word spacing
        if len(words) > 1:
            for i in range(len(words) - 1):
                spacing = words[i+1]["bbox"][2] - words[i]["bbox"][3]
                word_spacings.append(spacing)
    
    avg_word_spacing = np.mean(word_spacings) if word_spacings else 0
    word_heights = [word["bbox"][1] - word["bbox"][0] for word in all_words]
    avg_word_height = np.mean(word_heights) if word_heights else 0
    
    return {
        "num_lines": len(lines),
        "avg_line_height": float(avg_line_height),
        "line_height_variance": float(line_height_variance),
        "total_words": len(all_words),
        "avg_word_spacing": float(avg_word_spacing),
        "avg_word_height": float(avg_word_height),
        "lines": lines,  # for downstream processing
        "words": all_words
    }