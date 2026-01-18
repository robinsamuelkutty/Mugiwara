def get_dyscalculia_prompt(n: int) -> str:
    """
    Generates the prompt string for dyscalculia number generation.
    Does NOT make network calls.
    """
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

    Output format example:
    12021
    90906
    122112
    """
    return prompt.strip()