import random
import json
import re
import os
from dotenv import load_dotenv
import pandas as pd
from google import genai
from pathlib import Path



env_path = Path(__file__).resolve().parent/".env"
load_dotenv(env_path)  # loads .env into environment variables

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    # fallback (NOT recommended)
    raise ValueError("GEMINI_API_KEY not found in .env file")

# Difficulty CSV files (must contain a column named "word")
DIFFICULTY_FILES = {
    "easy": "easy.csv",
    "medium": "medium.csv",
    "hard": "hard.csv",
}

DEFAULT_DIFFICULTY = "medium"
WORDS_PER_STORY = 18
TARGET_SENTENCES = 7
MAX_ATTEMPTS = 1

# Start with a stable model
MODEL_NAME = "gemini-2.5-flash-lite"

# Create Gemini client once
client = genai.Client(api_key=API_KEY)


# ────────────────────────────────────────────────
# HELPERS
# ────────────────────────────────────────────────

def load_words(difficulty: str) -> list[str]:
    """Load words from the corresponding difficulty CSV file"""
    diff_key = difficulty.lower().strip()
    file_path = DIFFICULTY_FILES.get(diff_key)

    if not file_path:
        raise ValueError(
            f"Unknown difficulty level: '{difficulty}'. "
            f"Available: {list(DIFFICULTY_FILES.keys())}"
        )

    df = pd.read_csv(file_path)

    if "word" not in df.columns:
        raise ValueError(f"CSV '{file_path}' must contain a column named 'word'")

    words = df["word"].dropna().astype(str).str.strip().tolist()

    if not words:
        raise ValueError(f"No words found in {file_path}")

    return words


def extract_json(text: str) -> dict:
    """
    Extract JSON safely even if Gemini adds extra text or markdown fences.
    """
    text = (text or "").strip()

    # Remove markdown fences if present
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    # Extract JSON object from anywhere in the response
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in response")

    return json.loads(match.group(0))


def generate_dynamic_theme(age: int, gender: str | None = None) -> str:
    """Generate a short family-friendly story theme based on age (+ optional gender)"""

    # Age grouping (simple + safe)
    if age <= 5:
        age_group = "very young kids (3-5 years)"
        complexity = "very simple words"
    elif age <= 8:
        age_group = "young kids (6-8 years)"
        complexity = "simple words"
    elif age <= 12:
        age_group = "kids (9-12 years)"
        complexity = "simple but slightly longer words"
    else:
        age_group = "teenagers (13+ years)"
        complexity = "simple but interesting vocabulary"

    # Gender preference (optional)
    gender_line = ""
    if gender:
        gender = gender.lower().strip()
        if gender in ["boy", "male"]:
            gender_line = "Make the theme slightly appealing to a boy."
        elif gender in ["girl", "female"]:
            gender_line = "Make the theme slightly appealing to a girl."
        else:
            gender_line = "Keep the theme gender-neutral."

    prompt = f"""
Create ONE short, fun, family-friendly story idea.
8-15 words maximum.

Target reader: {age_group}
Use {complexity}.
Avoid scary, violent, or sad themes.
No romance.
No bullying.

{gender_line}

Output only the theme sentence, nothing else.

Examples:
- A little bird learns to fly higher each day
- A friendly robot helps fix broken toys
- A curious kitten finds a hidden garden
"""

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        return (response.text or "").strip()
    except Exception as e:
        print(f"Theme generation failed: {e}")
        return "A little animal has a small adventure"

# ────────────────────────────────────────────────
# MAIN STORY GENERATOR
# ────────────────────────────────────────────────

def generate_dyslexia_story(
    theme: str = None,
    difficulty: str = DEFAULT_DIFFICULTY,
    words_count: int = WORDS_PER_STORY,
    target_sentences: int = TARGET_SENTENCES
) -> dict:
    """
    Generate a short story where EVERY sentence contains at least ONE word
    from the selected difficulty word list.

    Returns:
    {
      'theme': str,
      'story': str,
      'success': bool,
      'used_words': list[str],
      'attempts': int
    }
    """

    if theme is None:
        theme = generate_dynamic_theme(age=8, gender="girl")


    # Load and sample words
    all_words = load_words(difficulty)
    selected_words = random.sample(all_words, min(words_count, len(all_words)))

    words_str = ", ".join(f'"{w}"' for w in selected_words)
    words_set = set(w.lower() for w in selected_words)

    prompt = f"""You are a gentle storyteller who writes for easy reading.

STRICT RULES:
1. EVERY sentence MUST contain at least ONE word from this list: {words_str}
2. Use very SHORT sentences only. Maximum 8-10 words each.
3. Use simple, clear words.
4. Write a short story: only {target_sentences} to {target_sentences + 3} sentences.
5. Make the story kind, fun and positive.
6. Never mention the word list, dyslexia, or any special rules.

Theme: {theme}

Output ONLY valid JSON in this exact format:
{{
  "story": "Full story text here. Sentences separated by spaces.",
  "sentences": ["Sentence one.", "Sentence two.", "Sentence three."]
}}
"""

    last_story = "Could not generate story"

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )

            raw = (response.text or "").strip()

            # Debug (enable if needed)
            # print("\nRAW OUTPUT:\n", raw)

            data = extract_json(raw)

            full_story = str(data.get("story", "")).strip()
            sentences = data.get("sentences", [])

            if not isinstance(sentences, list):
                raise ValueError("JSON field 'sentences' must be a list")

            # Validate: every sentence contains at least one chosen word
            missing = [
                s for s in sentences
                if isinstance(s, str) and not any(word in s.lower() for word in words_set)
            ]

            if not missing and full_story:
                return {
                    "theme": theme,
                    "story": full_story,
                    "success": True,
                    "used_words": selected_words,
                    "attempts": attempt
                }

            print(f"Attempt {attempt}: {len(missing)} sentences missing words → retrying")
            last_story = full_story if full_story else last_story

        except Exception as e:
            print(f"Attempt {attempt} failed: {e}")

    return {
        "theme": theme,
        "story": last_story,
        "success": False,
        "used_words": selected_words,
        "attempts": MAX_ATTEMPTS
    }


def print_story_result(result: dict):
    """Pretty print the result"""
    print("\n" + "=" * 60)
    print("THEME:", result["theme"])
    print("-" * 60)
    print(result["story"])
    print("-" * 60)
    print(f"Success: {result['success']}  |  Attempts: {result['attempts']}")
    print(f"Difficulty: {DEFAULT_DIFFICULTY}  |  Words used: {len(result['used_words'])}")
    print("=" * 60 + "\n")


# ────────────────────────────────────────────────
# RUN
# ────────────────────────────────────────────────

if __name__ == "__main__":
    print("Dyslexia Story Generator (google.genai)")
    print("--------------------------------------\n")

    result = generate_dyslexia_story(
        difficulty="medium",
        # theme="A small puppy finds a new friend"
    )

    print_story_result(result)



def extract_json(text: str) -> dict:
    """
    Extract JSON safely even if Gemini adds extra text or markdown fences.
    """
    text = (text or "").strip()

    # Remove markdown fences if present
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    # Extract JSON object from anywhere in the response
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in response")

    return json.loads(match.group(0))


def generate_dynamic_theme(age: int, gender: str | None = None) -> str:
    """Generate a short family-friendly story theme based on age (+ optional gender)"""

    # Age grouping (simple + safe)
    if age <= 5:
        age_group = "very young kids (3-5 years)"
        complexity = "very simple words"
    elif age <= 8:
        age_group = "young kids (6-8 years)"
        complexity = "simple words"
    elif age <= 12:
        age_group = "kids (9-12 years)"
        complexity = "simple but slightly longer words"
    else:
        age_group = "teenagers (13+ years)"
        complexity = "simple but interesting vocabulary"

    # Gender preference (optional)
    gender_line = ""
    if gender:
        gender = gender.lower().strip()
        if gender in ["boy", "male"]:
            gender_line = "Make the theme slightly appealing to a boy."
        elif gender in ["girl", "female"]:
            gender_line = "Make the theme slightly appealing to a girl."
        else:
            gender_line = "Keep the theme gender-neutral."

    prompt = f"""
Create ONE short, fun, family-friendly story idea.
8-15 words maximum.

Target reader: {age_group}
Use {complexity}.
Avoid scary, violent, or sad themes.
No romance.
No bullying.

{gender_line}

Output only the theme sentence, nothing else.

Examples:
- A little bird learns to fly higher each day
- A friendly robot helps fix broken toys
- A curious kitten finds a hidden garden
"""

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        return (response.text or "").strip()
    except Exception as e:
        print(f"Theme generation failed: {e}")
        return "A little animal has a small adventure"

# ────────────────────────────────────────────────
# MAIN STORY GENERATOR
# ────────────────────────────────────────────────

def generate_dyslexia_story(
    theme: str = None,
    difficulty: str = DEFAULT_DIFFICULTY,
    words_count: int = WORDS_PER_STORY,
    target_sentences: int = TARGET_SENTENCES
) -> dict:
    """
    Generate a short story where EVERY sentence contains at least ONE word
    from the selected difficulty word list.

    Returns:
    {
      'theme': str,
      'story': str,
      'success': bool,
      'used_words': list[str],
      'attempts': int
    }
    """

    if theme is None:
        theme = generate_dynamic_theme(age=8, gender="girl")


    # Load and sample words
    all_words = load_words(difficulty)
    selected_words = random.sample(all_words, min(words_count, len(all_words)))

    words_str = ", ".join(f'"{w}"' for w in selected_words)
    words_set = set(w.lower() for w in selected_words)

    prompt = f"""You are a gentle storyteller who writes for easy reading.

STRICT RULES:
1. EVERY sentence MUST contain at least ONE word from this list: {words_str}
2. Use very SHORT sentences only. Maximum 8-10 words each.
3. Use simple, clear words.
4. Write a short story: only {target_sentences} to {target_sentences + 3} sentences.
5. Make the story kind, fun and positive.
6. Never mention the word list, dyslexia, or any special rules.

Theme: {theme}

Output ONLY valid JSON in this exact format:
{{
  "story": "Full story text here. Sentences separated by spaces.",
  "sentences": ["Sentence one.", "Sentence two.", "Sentence three."]
}}
"""

    last_story = "Could not generate story"

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )

            raw = (response.text or "").strip()

            # Debug (enable if needed)
            # print("\nRAW OUTPUT:\n", raw)

            data = extract_json(raw)

            full_story = str(data.get("story", "")).strip()
            sentences = data.get("sentences", [])

            if not isinstance(sentences, list):
                raise ValueError("JSON field 'sentences' must be a list")

            # Validate: every sentence contains at least one chosen word
            missing = [
                s for s in sentences
                if isinstance(s, str) and not any(word in s.lower() for word in words_set)
            ]

            if not missing and full_story:
                return {
                    "theme": theme,
                    "story": full_story,
                    "success": True,
                    "used_words": selected_words,
                    "attempts": attempt
                }

            print(f"Attempt {attempt}: {len(missing)} sentences missing words → retrying")
            last_story = full_story if full_story else last_story

        except Exception as e:
            print(f"Attempt {attempt} failed: {e}")

    return {
        "theme": theme,
        "story": last_story,
        "success": False,
        "used_words": selected_words,
        "attempts": MAX_ATTEMPTS
    }


def print_story_result(result: dict):
    """Pretty print the result"""
    print("\n" + "=" * 60)
    print("THEME:", result["theme"])
    print("-" * 60)
    print(result["story"])
    print("-" * 60)
    print(f"Success: {result['success']}  |  Attempts: {result['attempts']}")
    print(f"Difficulty: {DEFAULT_DIFFICULTY}  |  Words used: {len(result['used_words'])}")
    print("=" * 60 + "\n")


# ────────────────────────────────────────────────
# RUN
# ────────────────────────────────────────────────

if __name__ == "__main__":
    print("Dyslexia Story Generator (google.genai)")
    print("--------------------------------------\n")

    result = generate_dyslexia_story(
        difficulty="medium",
        # theme="A small puppy finds a new friend"
    )

    print_story_result(result)