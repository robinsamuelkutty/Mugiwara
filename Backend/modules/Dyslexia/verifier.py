import os
import json
from typing import Dict, Any
from dotenv import load_dotenv
from pathlib import Path
# Gemini SDK (new)
from google import genai



env_path = Path(__file__).resolve().parent/".env"
load_dotenv(env_path)  # loads .env into environment variables

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def verify_with_gemini(level_results: Dict[int, Any]) -> Dict[str, Any]:
    """
    level_results contains all 4 level evidence:
    {
      1: {...},
      2: {...},
      3: {...},
      4: {...}
    }
    """

    if not GEMINI_API_KEY:
        return {
            "final_result": "INCONCLUSIVE",
            "confidence": 0.0,
            "reason": "Gemini API key missing"
        }

    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = f"""
You are an educational screening assistant.

Task:
Given 4-level reading test evidence, decide the screening outcome.

You MUST output ONLY valid JSON in this exact format:
{{
  "final_result": "NORMAL" | "RISK_DYSLEXIA" | "INCONCLUSIVE",
  "confidence": 0.0 to 1.0,
  "reason": "short explanation"
}}

Rules:
- Do NOT diagnose medically.
- Use consistency across levels.
- Strong dyslexia evidence = consistent decoding issues + low nonsense word performance.
- If results are mixed or unclear -> INCONCLUSIVE.
- Output ONLY raw JSON text. Do NOT wrap it inside ```json or any code block.

Evidence:
{json.dumps(level_results, indent=2)}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    text = (response.text or "").strip()

    # --- remove markdown code fences like ```json ... ``` ---
    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()

    # --- try parsing JSON safely ---
    try:
        return json.loads(text)
    except Exception:
        # fallback: extract JSON object from text
        try:
            start = text.index("{")
            end = text.rindex("}") + 1
            return json.loads(text[start:end])
        except Exception:
            return {
                "final_result": "INCONCLUSIVE",
                "confidence": 0.0,
                "reason": f"Gemini output not valid JSON: {text[:200]}"
            }