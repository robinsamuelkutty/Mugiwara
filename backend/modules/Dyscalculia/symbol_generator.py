from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

def get_dyscalculia_inducing_digits(n: int):
    prompt = f"""
Generate exactly {n} dyscalculia-inducing digit strings using ONLY digits 0-9.

Rules:
- Each item must be a digit string (length 4 to 8)
- Use ONLY digits (no spaces inside an item, no symbols, no words)
- Output one item per line
- No explanations, no numbering, no extra text

Make the patterns tricky by using:
- reversals (e.g., 1234 vs 4321)
- transpositions (swap middle digits)
- repeated digits (e.g., 889988)
- alternating patterns (e.g., 121212)
- near-similar sequences (e.g., 1001, 1010, 1100)

Output format example:
12021
90906
122112
"""

    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt.strip()
    )

    return response.text.strip()


if __name__ == "__main__":
    output = get_dyscalculia_inducing_digits(n=8)
    print("\n✅ Dyscalculia-inducing digit strings:\n")
    print(output)
