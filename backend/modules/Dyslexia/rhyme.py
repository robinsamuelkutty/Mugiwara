import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai

env_path = Path(__file__).resolve().parent.parent.parent/".env"
load_dotenv(env_path)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def generate_rhyming_pair(level="easy"):
    prompt = f"""
Generate ONE pair of English rhyming words for kids dyslexia test.
Rules:
- Output only 2 words separated by a comma.
- No sentences.
- Must be common and simple words.
- Difficulty: {level}
Examples:
cat, hat
book, look
rain, train
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    text = response.text.strip()

    # safety cleanup
    text = text.replace("\n", "").replace(" ", "")
    words = text.split(",")

    if len(words) != 2:
        return None

    return words[0], words[1]


if __name__ == "__main__":
    pair = generate_rhyming_pair("easy")
    print(pair)
