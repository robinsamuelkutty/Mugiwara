import requests

FASTAPI_URL = "http://127.0.0.1:8000/generate"


def build_prompt():
    return """
Generate dyslexia/dyscalculia-inducing ADDITION questions.

Create exactly 25 questions, grouped in this exact order:

1) Reversal / Transposition prone (5 questions)
   - Use swapped digits like 14+41, 23+32, 16+61

2) Carry confusion (5 questions)
   - Two-digit + two-digit where at least one carry happens

3) Repeated digits (5 questions)
   - Use patterns like 22+33, 44+11, 55+22

4) Zeros / place value confusion (5 questions)
   - Use numbers with 0 like 10+19, 20+18, 30+17

5) Similar-looking digit patterns (5 questions)
   - Use numbers like 88+11, 99+12, 69+96, 78+87

STRICT OUTPUT FORMAT:
- Output ONLY the questions
- make the questions random
- One question per line
- No numbering, no headings, no explanations
- Format exactly like: number + number
""".strip()


def fetch_questions(max_new_tokens:int):
    payload = {
        "prompt": build_prompt(),
        "max_new_tokens": max_new_tokens
    }

    res = requests.post(FASTAPI_URL, json=payload, timeout=120)
    res.raise_for_status()
    data = res.json()

    full_text = data.get("response", "")
    return full_text


def clean_questions(text: str):
    """
    Extract valid lines like: '10 + 19'
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    valid = []

    for line in lines:
        # Keep only lines that contain '+' and digits
        if "+" in line:
            # Remove any accidental numbering like "1) 10 + 19"
            line = line.replace(")", "").replace(".", "")
            parts = line.split("+")
            if len(parts) == 2:
                left = parts[0].strip()
                right = parts[1].strip()

                if left.isdigit() and right.isdigit():
                    valid.append(f"{left} + {right}")

    return valid


if __name__ == "__main__":
    print("\n📌 Fetching dyscalculia-inducing addition questions from LLM...\n")

    raw = fetch_questions(400)
    questions = clean_questions(raw)

    print("✅ Questions received:", len(questions))
    print("\n--- Questions ---\n")

    for q in questions:
        print(q)