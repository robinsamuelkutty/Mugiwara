"""
Role: CLIP-based image–text semantic similarity
Used to validate whether handwritten image matches intended sentence
"""

import torch
import clip
from PIL import Image
import torch.nn.functional as F

# Device selection
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Load model ONCE
clip_model, clip_preprocess = clip.load("ViT-B/32", device=DEVICE)
clip_model.eval()


def compute_clip_similarity(image_pil, expected_text):
    image = clip_preprocess(image_pil).unsqueeze(0).to(DEVICE)

    prompts = [
        f"a neat handwritten sentence written clearly on a rules or blank paper: {expected_text}"
    ]

    text_tokens = clip.tokenize(prompts).to(DEVICE)

    with torch.no_grad():
        image_features = clip_model.encode_image(image)
        text_features = clip_model.encode_text(text_tokens)

        image_features = F.normalize(image_features, dim=-1)
        text_features = F.normalize(text_features, dim=-1)

        similarity = (image_features @ text_features.T).item()
        logits = (image_features @ text_features.T).softmax(dim=-1)

        print(image_features.norm().item())
        print(text_features.norm().item())


    # Probability that image matches the intended sentence
    return similarity
