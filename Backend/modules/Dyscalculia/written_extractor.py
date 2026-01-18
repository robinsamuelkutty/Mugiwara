import base64
import requests

OLLAMA_VISION_URL = "http://127.0.0.1:8000/generate"
VISION_MODEL = "llava:7b"   # install: ollama pull llava


def encode_image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def extract_digits_from_image(image_path: str) -> str:
    """
    Uses Ollama Vision model to extract only digits from the image.
    """
    image_b64 = encode_image_to_base64(image_path)

    prompt = """
You are analyzing a dyscalculia screening test.
The image contains digits written by a child.

TASK:
Extract ONLY the digits in the exact order they appear.

STRICT RULES:
- Output ONLY digits (0-9)
- No spaces, no new lines
- No explanations, no extra text

Example output:
13574
"""

    payload = {
        "model": "llava:7b",
        "prompt": prompt.strip(),
        "stream": False,
        "images": [image_b64],
    }

    r = requests.post(OLLAMA_VISION_URL, json=payload, timeout=120)
    r.raise_for_status()

    data = r.json()
    return data.get("response", "").strip()


def compare_digits(original: str, extracted: str):
    """
    Compare original digit string with extracted digit string.
    Returns mismatch details with index positions.
    """
    mismatches = []

    min_len = min(len(original), len(extracted))

    # compare common length
    for i in range(min_len):
        if original[i] != extracted[i]:
            mismatches.append({
                "index": i,
                "expected": original[i],
                "got": extracted[i]
            })

    # if extracted shorter
    if len(extracted) < len(original):
        for i in range(len(extracted), len(original)):
            mismatches.append({
                "index": i,
                "expected": original[i],
                "got": None
            })

    # if extracted longer
    if len(extracted) > len(original):
        for i in range(len(original), len(extracted)):
            mismatches.append({
                "index": i,
                "expected": None,
                "got": extracted[i]
            })

    return mismatches


def main():
    print("\n=== Written Digit Extractor (Dyscalculia Test) ===\n")

    """
    image_path = input("Enter image path (example: sample.jpg): ").strip()
    original = input("Enter original digit string (example: 13574): ").strip()
    """

    image_path="test.jpg"
    original = "43241"
    print("\n🔍 Extracting digits from image using Ollama Vision...\n")
    extracted = extract_digits_from_image(image_path)

    print("✅ Original :", original)
    print("🧠 Extracted:", extracted)
    mismatches = compare_digits(original, extracted)

    if not mismatches:
        print("\n🎉 Perfect match! No dyslexical/dyscalculic digit confusion detected.")
    else:
        print("\n⚠️ Mismatches found (possible digit confusion):\n")
        for m in mismatches:
            print(f"Index {m['index']} | Expected: {m['expected']} | Got: {m['got']}")


if __name__ == "__main__":
    main()