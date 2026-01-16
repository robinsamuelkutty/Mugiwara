import os
import re
from dotenv import load_dotenv
from google import genai
from pathlib import Path
env_path = Path(__file__).resolve().parent.parent.parent/".env"
load_dotenv(env_path)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY not found in .env")

client = genai.Client(api_key=GEMINI_API_KEY)

MODEL_NAME = "gemini-2.5-flash"


def compute_answer(question: str) -> int:
    """
    Supports simple addition like: '18 + 27'
    """
    q = question.replace(" ", "")
    if "+" not in q:
        raise ValueError("Only addition is supported (example: 18 + 27)")
    a, b = q.split("+")
    return int(a) + int(b)


def extract_digits_only(text: str):
    """
    Extract first integer from model output.
    """
    match = re.search(r"\d+", text)
    if match:
        return int(match.group())
    return None


def check_answer_from_image(image_path: str, question: str):
    correct = compute_answer(question)

    prompt = f"""
You are checking a dyscalculia screening test.

Question: {question}
Correct Answer: {correct}

The child wrote the answer in the image.

TASKS:
1) Extract ONLY the written answer number from the image.
2) Compare it with the correct answer.
3) Return the result in EXACTLY this format:

WrittenAnswer: <number>
CorrectAnswer: <number>
Result: Correct OR Wrong
Explanation: <one short sentence>

STRICT RULES:
- WrittenAnswer must be digits only
- Explanation must be short and simple
- No extra lines other than the 4 lines
"""

    uploaded = client.files.upload(file=image_path)

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[prompt.strip(), uploaded]
    )

    return response.text.strip()


def main():
    print("\n=== Gemini Math Image Answer Checker ===\n")

    # Example values (change these)
    image_path = "answer.jpg"
    question = "14 + 41"

    result_text = check_answer_from_image(image_path, question)

    print("\n📌 Gemini Output:\n")
    print(result_text)

    # Optional: local verification (extra safety)
    correct = compute_answer(question)
    written = extract_digits_only(result_text)

    if written is not None:
        print("\n✅ Local Verification:")
        print("Written Answer:", written)
        print("Correct Answer:", correct)
        print("Match:", written == correct)


if __name__ == "__main__":
    main()
