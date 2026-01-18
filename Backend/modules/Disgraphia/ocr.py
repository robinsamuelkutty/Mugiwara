"""
ocr.py
Role: Line-wise handwritten OCR extraction with optimized Tesseract config
Receives: OCR-ready binary image (numpy array)
Returns: extracted text string

Tuned for:
  - Handwritten text (not printed)
  - Cursive/connected script
  - Children's handwriting (ages 5-15)
"""

import pytesseract
from PIL import Image
import numpy as np
import cv2


def extract_text(preprocessed_image):
    """
    Extract text from handwritten image using Tesseract.

    Input: OCR-ready binary image (numpy array)
    Output: extracted text string

    Uses optimized PSM and OEM for handwriting recognition.
    """

    # Convert OpenCV image to PIL for Tesseract
    pil_image = Image.fromarray(preprocessed_image)
    pytesseract.pytesseract.tesseract_cmd = (
        r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    )

    # Tesseract config TUNED for handwriting:
    # --oem 2: LSTM-only (better for handwriting)
    # --psm 6: Assume a single uniform block of text (handles multi-line + varying layout)
    # -c tessedit_char_whitelist: restrict to alphanumeric + punctuation
    custom_config = r'--oem 3 --psm 11 -l eng'

    try:
        text = pytesseract.image_to_string(
            pil_image,
            config=custom_config,
            lang='eng'
        )
    except Exception as e:
        # Fallback: try without lang specification
        text = pytesseract.image_to_string(pil_image, config=custom_config)

    # Post-processing: normalize whitespace
    text = text.strip()
    text = " ".join(text.split())
    print("\n===== OCR EXTRACTED TEXT =====")
    print(text)
    print("===== END OCR TEXT =====\n")

    return text


def extract_text_with_confidence(preprocessed_image):
    """
    Extract text WITH confidence scores (advanced).
    Useful for debugging OCR quality.

    Returns: (text, avg_confidence)
    """

    pil_image = Image.fromarray(preprocessed_image)

    custom_config = r'--oem 2 --psm 6'

    # Get detailed output
    data = pytesseract.image_to_data(pil_image, config=custom_config, output_type=pytesseract.Output.DICT)

    # Extract text and average confidence
    text_parts = []
    confidences = []

    for i, conf in enumerate(data['conf']):
        if conf > 0:  # Only include recognized characters
            text_parts.append(data['text'][i])
            confidences.append(conf)

    text = " ".join(text_parts)
    avg_confidence = np.mean(confidences) if confidences else 0.0

    return text.strip(), float(avg_confidence)


def prepare_image_for_clip(preprocessed_image):
    """
    Convert OCR-preprocessed image back to RGB PIL format for CLIP.
    CLIP requires natural image statistics.
    """

    if len(preprocessed_image.shape) == 2:
        # grayscale → RGB
        rgb = cv2.cvtColor(preprocessed_image, cv2.COLOR_GRAY2RGB)
    else:
        rgb = preprocessed_image

    return Image.fromarray(rgb)