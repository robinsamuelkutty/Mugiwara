import os
from dotenv import load_dotenv
from google import genai
from pathlib import Path
env_path = Path(__file__).resolve().parent.parent.parent/".env"
load_dotenv(env_path)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY not found in .env file")

client = genai.Client(api_key=GEMINI_API_KEY)

MODEL_NAME = "gemini-2.5-flash"   # fast + supports vision


def extract_digits_from_image(image_path: str) -> str:
    """
    Upload image to Gemini and extract only digits.
    """
    prompt = """
    You are analyzing a dyscalculia screening test.

    The image contains digits written by a child as part of the screening.
    Your task is to judge whether the writing pattern shows signs consistent with dyscalculia.

    EVALUATE BASED ON:
    - frequent digit reversals or mirroring
    - inconsistent number formation
    - confusion between similar digits (e.g., 2/5, 6/9, 3/8)
    - irregular sequencing or missing digits
    - poor number representation that suggests number-symbol difficulty

    IMPORTANT:
    This is only a screening decision based on this single sample (not a diagnosis).

    OUTPUT FORMAT (STRICT):
    Return exactly 2 lines:

    Line 1: One label only:
    LIKELY_DYSCALCULIA
    or
    UNLIKELY_DYSCALCULIA

    Line 2: Reason in 1-2 short sentences, referring only to what is visible in the image.

    Do not output anything else.
    """

    uploaded = client.files.upload(file=image_path)

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[prompt, uploaded]
    )

    return response.text.strip()


def compare_digits(original: str, extracted: str):
    """
    Compare original digit string with extracted digit string.
    Returns mismatch details with index positions.
    """
    mismatches = []
    min_len = min(len(original), len(extracted))

    for i in range(min_len):
        if original[i] != extracted[i]:
            mismatches.append({
                "index": i,
                "expected": original[i],
                "got": extracted[i]
            })

    if len(extracted) < len(original):
        for i in range(len(extracted), len(original)):
            mismatches.append({
                "index": i,
                "expected": original[i],
                "got": None
            })

    if len(extracted) > len(original):
        for i in range(len(original), len(extracted)):
            mismatches.append({
                "index": i,
                "expected": None,
                "got": extracted[i]
            })

    return mismatches


def main():
    print("\n=== Written Digit Extractor (Gemini Vision) ===\n")

    image_path = "test.jpg"
    original = "43241"

    print("🔍 Extracting digits from image using Gemini...\n")
    extracted = extract_digits_from_image(image_path)

    print("✅ Original :", original)
    print("🧠 Extracted:", extracted)

    mismatches = compare_digits(original, extracted)

    if not mismatches:
        print("\n🎉 Perfect match! No digit confusion detected.")
    else:
        print("\n⚠️ Mismatches found (possible digit confusion):\n")
        print(extracted)


if __name__ == "__main__":
    main()