import base64
import json
import os
from pathlib import Path
from typing import Dict, Any

from dotenv import load_dotenv
from google import genai


class NumberExtractor:
    """
    Extract numbers from handwritten images using Google Gemini API
    Optimized for dyscalculia handwriting
    """

    def __init__(self):
        # Load .env from backend/.env
        env_path = Path(__file__).resolve().parent.parent.parent / ".env"
        load_dotenv(env_path)

        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in .env")

        self.client = genai.Client(api_key=self.api_key)
        self.model_name = "gemini-2.5-flash"

    def load_image_base64(self, image_path: str) -> str:
        """Load and encode image to base64"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def extract_numbers(self, image_path: str) -> Dict[str, Any]:
        """
        Extract numbers from handwritten image using Gemini Vision
        Returns extracted numbers and analysis
        """

        prompt = """
You are analyzing a handwritten number image for a dyscalculia screening test.

Step 1: Extract ALL digits/numbers visible in the image (left to right).
Step 2: Identify writing patterns that may indicate difficulty with number formation.

Look for:
- digit reversals (2, 3, 5, 6, 7, 9)
- mirror writing
- digit substitutions (e.g., 6↔9, 1↔7, 3↔8)
- inconsistent spacing or ordering
- unclear or malformed digits

IMPORTANT:
- Do NOT give a medical diagnosis.
- Output only a screening-style risk assessment.

Output ONLY raw JSON (no markdown fences) in this exact format:
{
  "digits": ["..."],
  "complete_number": "...",
  "digit_analysis": [
    {"digit": "...", "confidence": "high/medium/low", "issues": ["reversal/malformed/unclear/none"], "notes": "..."}
  ],
  "observations": ["..."],
  "screening_risk": {
    "risk_level": "LOW" | "MEDIUM" | "HIGH",
    "reason": "short explanation"
  }
}
"""

        if not os.path.exists(image_path):
            return {"error": f"Image not found: {image_path}"}

        with open(image_path, "rb") as f:
            img_bytes = f.read()

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[
                prompt,
                {
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": base64.b64encode(img_bytes).decode("utf-8"),
                    }
                },
            ],
        )

        response_text = (response.text or "").strip()

        # Remove markdown fences if Gemini adds them
        if response_text.startswith("```"):
            response_text = response_text.replace("```json", "").replace("```", "").strip()

        # Extract JSON from response
        try:
            start = response_text.index("{")
            end = response_text.rindex("}") + 1
            json_str = response_text[start:end]
            return json.loads(json_str)
        except Exception:
            return {"raw_response": response_text}

    def process_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Pretty print extraction results"""
        print("\n" + "=" * 70)
        print("EXTRACTION RESULTS")
        print("=" * 70)

        if "complete_number" in result:
            print(f"\n✓ Extracted Number: {result.get('complete_number')}")
            print(f"  Digits: {' '.join(result.get('digits', []))}")

            if "observations" in result:
                print("\n  Observations:")
                for obs in result.get("observations", []):
                    print(f"   - {obs}")

            if "screening_risk" in result:
                risk = result["screening_risk"]
                print("\n  Screening Risk:")
                print(f"   - Level: {risk.get('risk_level')}")
                print(f"   - Reason: {risk.get('reason')}")
        else:
            print("\nRaw Response:")
            print(result)

        return result

    def save_results(self, result: Dict[str, Any], output_file: str = "extraction_results.json"):
        """Save results to JSON file"""
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print(f"\n✓ Results saved to: {output_file}")


def main():
    import sys

    print("\n" + "█" * 70)
    print("GOOGLE GEMINI API - NUMBER EXTRACTION")
    print("█" * 70)

    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        image_path = input("Enter image path: ").strip()

    extractor = NumberExtractor()
    result = extractor.extract_numbers(image_path)
    extractor.process_result(result)
    extractor.save_results(result)
    print("\n✓ COMPLETE")


if __name__ == "__main__":
    main()