# dysgraphia/vit_features.py
"""
Role: Vision Transformer based handwriting structure embedding
Purpose: Capture stroke rhythm, layout consistency, visual regularity
"""

import torch
from transformers import ViTImageProcessor, ViTModel
from PIL import Image
import numpy as np

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

processor = ViTImageProcessor.from_pretrained(
    "google/vit-base-patch16-224"
)
vit_model = ViTModel.from_pretrained(
    "google/vit-base-patch16-224"
).to(DEVICE)
vit_model.eval()


def extract_vit_embedding(image_pil: Image.Image) -> np.ndarray:
    """
    Input: RGB PIL image
    Output: 768-dim embedding (CLS token)
    """
    inputs = processor(images=image_pil, return_tensors="pt")
    inputs = {k: v.to(DEVICE) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = vit_model(**inputs)

    cls_embedding = outputs.last_hidden_state[:, 0, :]  # CLS token
    return cls_embedding.squeeze(0).cpu().numpy()

def vit_structure_score(embedding: np.ndarray) -> float:
    """
    Higher variance = more irregular handwriting structure
    Output normalized to 0–1
    """
    variance = np.var(embedding)
    score = min(1.0, variance / 1.5)
    return float(score)
