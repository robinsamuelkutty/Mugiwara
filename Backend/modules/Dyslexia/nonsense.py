import os
from dotenv import load_dotenv
from google import genai
from pathlib import Path

# Fix path to look in the same folder
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(env_path)

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def nonesense_generator():
    prompt = """
    Generate 5 nonsense words for a dyslexia screening test.
    Rules:
    - Must be meaningless but pronounceable (pseudowords).
    - Mix of patterns: b/d flips (e.g., 'bep'), blends (e.g., 'strop'), and digraphs (e.g., 'thip').
    - Output ONLY the words separated by spaces. 
    - NO newlines, NO bullet points, NO extra text.
    
    Example Output:
    zog pleet brimpf dresp thazz
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-lite", 
            contents=prompt
        )
        # Clean up response to ensure it's just a string of words
        text = response.text.replace("\n", " ").strip()
        return {"words": text}
        
    except Exception as e:
        print(f"Error: {e}")
        return {"words": "zog pleet brimpf dresp thazz"}

if __name__ == "__main__":
    print(nonesense_generator())