"""
preprocessor.py
Role: OCR-specific image preprocessing pipeline with enhanced robustness
Receives: raw image bytes
Returns: OCR-ready binary image (numpy array)

8-stage pipeline addressing discovered issues:
  - Polarity (correct black text on white)
  - Lighting sensitivity (CLAHE contrast enhancement)
  - Noise & skew (median blur, adaptive binarization, deskew)
  - Handwriting-specific (morphology closing for connected strokes)
"""

import cv2
import numpy as np


def preprocess_for_ocr(file_bytes: bytes):
    """
    8-stage OCR preprocessing pipeline.
    Input: raw image bytes
    Output: OCR-ready binary image (numpy array)
    """

    # ---------- Stage 1: Decode image ----------
    image_array = np.frombuffer(file_bytes, np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    if image is None:
        raise ValueError("Invalid image file")

    h, w, _ = image.shape
    if h < 300 or w < 300:
        raise ValueError("Image resolution too low for OCR (min 300x300)")

    # ---------- Stage 2: Grayscale conversion ----------
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # ---------- Stage 3: Noise removal (median + bilateral) ----------
    # Median blur removes salt-and-pepper noise
    denoised = cv2.medianBlur(gray, 5)
    # Bilateral filter preserves edges while smoothing
    denoised = cv2.bilateralFilter(denoised, 9, 75, 75)

    # ---------- Stage 4: Contrast enhancement (CLAHE) ----------
    # Addresses lighting sensitivity, improves local contrast
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(10, 10))
    enhanced = clahe.apply(denoised)

    # ---------- Stage 5: Morphological opening ----------
    # Remove small white noise before binarization
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    opened = cv2.morphologyEx(enhanced, cv2.MORPH_OPEN, kernel)

    # ---------- Stage 6: Adaptive binarization (aggressive) ----------
    # THRESH_BINARY_INV: converts to black text on white background
    # Larger blockSize for better adaptation to lighting
    binary = cv2.adaptiveThreshold(
        opened,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        21,  # larger blockSize for smoother thresholding
        5    # stricter C value
    )

    # ---------- Stage 7: Skew correction ----------
    # Detect text angle and rotate to horizontal
    coords = np.column_stack(np.where(binary > 0))
    
    if len(coords) < 10:
        raise ValueError("Insufficient handwriting content in image")
    
    angle = cv2.minAreaRect(coords)[-1]

    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    h, w = binary.shape
    M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
    deskewed = cv2.warpAffine(
        binary,
        M,
        (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE
    )

    # ---------- Stage 8: Morphological closing ----------
    # Close gaps in connected strokes (important for cursive handwriting)
    kernel_close = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    closed = cv2.morphologyEx(deskewed, cv2.MORPH_CLOSE, kernel_close)
    
    # Final small dilation to strengthen characters
    kernel_dilate = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
    refined = cv2.dilate(closed, kernel_dilate, iterations=1)

    return refined