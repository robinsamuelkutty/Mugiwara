import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai
import json

# --- 🛠 FIX: Look for .env in the SAME folder as this file ---
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(env_path)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError(f"❌ API Key not found! Please check your .env file at: {env_path}")

client = genai.Client(api_key=api_key)

def generate_rhyming_set(level="easy"):
    prompt = f"""
    Generate 10 pairs of English rhyming words for a dyslexia test.
    
    Rules:
    - Output strictly a JSON list of strings.
    - Each string should contain two words separated by a space.
    - No punctuation like commas.
    - Level: {level}
    
    Example Output format:
    ["cat hat", "sun run", "blue shoe"]
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash", # Changed to 2.0-flash (standard stable version)
            contents=prompt,
            config={'response_mime_type': 'application/json'} # Force JSON output
        )
        
        # Parse the JSON response
        rhyme_list = json.loads(response.text)
        return rhyme_list
        
    except Exception as e:
        print(f"Error generating rhymes: {e}")
        # Fallback list if AI fails
        return [
            "cat hat", "dog log", "fish dish", "sun run", "blue shoe",
            "pen hen", "map nap", "pig wig", "hot pot", "red bed"
        ]

if __name__ == "__main__":
    print(generate_rhyming_set())