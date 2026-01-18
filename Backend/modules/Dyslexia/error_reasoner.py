import os, json
from typing import Dict, Any, List
from dotenv import load_dotenv
from google import genai

load_dotenv()

def reason_negative_errors_with_gemini(level: int, negative_errors: List[Dict[str, Any]]) -> Dict[str, Any]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {
            "cause": "INCONCLUSIVE",
            "confidence": 0.0,
            "suggest_retest": False,
            "reason": "Missing GEMINI_API_KEY"
        }

    client = genai.Client(api_key=api_key)

    prompt = f"""
You are analyzing reading errors from a dyslexia screening test.

Given a list of incorrect word pairs, classify the most likely cause.

Output ONLY raw JSON:
{{
  "cause": "ACCENT_VARIATION" | "ASR_NOISE" | "DYSLEXIA_PATTERN" | "MIXED",
  "confidence": 0.0 to 1.0,
  "suggest_retest": true/false,
  "reason": "short explanation"
}}

Rules:
- Accent variation includes normal pronunciation differences.
- ASR noise includes transcription mistakes.
- Dyslexia pattern includes decoding/reversal/transposition patterns.
- If unsure -> MIXED.

Test Level: {level}
Negative Errors:
{json.dumps(negative_errors, indent=2)}
"""

    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    text = (resp.text or "").strip()

    # remove ```json fences if present
    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(text)
    except Exception:
        return {
            "cause": "INCONCLUSIVE",
            "confidence": 0.0,
            "suggest_retest": False,
            "reason": f"Invalid JSON from Gemini: {text[:200]}"
        }