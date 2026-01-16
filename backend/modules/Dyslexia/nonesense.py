import os
from dotenv import load_dotenv
from google import genai
from pathlib import Path
env_path = Path(__file__).resolve().parent.parent.parent/".env"
load_dotenv(env_path)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def nonesense_generator():
    prompt = """
Generate 6-8 nonsense words for dyslexia testing.
Rules:
- Must be meaningless words (not real dictionary words)
- Pronounceable like English
- Include a mix of short (3-4 letters), medium (5-7 letters), and long (8-12 letters)
- Include confusing patterns: b/d, p/q, m/n, th/sh/ch/ph, double letters
Output as a clean sentence seperated by blank space only.
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt
    )
    return response

#print(nonesense_generator().text)
