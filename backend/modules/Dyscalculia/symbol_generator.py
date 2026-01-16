import requests

FASTAPI_URL = "http://127.0.0.1:8000/generate"

def get_dyscalculia_inducing_letters(n:int):
    prompt = f"""
    Generate exactly {n} dyslexia-inducing digit strings using ONLY digits 0-9.

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
    -return expecially numbers or digits 

    Output format example:
    12021
    90906
    122112
    """

    payload = {
        "prompt": prompt.strip(),
        "max_new_tokens": 200
    }

    res = requests.post(FASTAPI_URL, json=payload, timeout=120)
    res.raise_for_status()

    data = res.json()
    return data.get("response", "")

if __name__ == "__main__":
    output = get_dyscalculia_inducing_letters(n=8)
    print("\n✅ Dyscalculia-inducing symbols:\n")
    print(output)
