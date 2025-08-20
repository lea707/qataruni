import os
import json
import re
from typing import Dict
from google import genai
from google.genai import types
from database.connection import SessionLocal
from models.skill_category import SkillCategory

def get_predefined_categories():
    """Fetch existing categories from database"""
    db = SessionLocal()
    try:
        categories = db.query(SkillCategory.category_name).distinct().all()
        return [category[0] for category in categories]
    except Exception as e:
        print(f"⚠️ Database error: {e}")
        return ["Technical Skills", "Programming Languages", "Soft Skills", "Language Skills"]
    finally:
        db.close()

def extract_skills_from_text(text: str) -> dict:
    """
    Extract skills from text using Gemini API with your proven working approach
    """
    api_key = os.getenv("GEMINI_API_KEY") or "AIzaSyAjDLkmiUQnleseIXcZaSyrruxR6OP5RRY"
    if not api_key:
        raise EnvironmentError("❌ GEMINI_API_KEY not set in environment.")

    client = genai.Client(api_key=api_key)
    model = "gemini-2.0-flash"  # Changed to a more reliable model

    predefined_categories = get_predefined_categories()
    
    # Clean and truncate text to avoid token limits
    text = text.strip()[:10000]  # Limit to 10k characters
    
    prompt = f"""
ANALYZE THIS TEXT AND EXTRACT PROFESSIONAL SKILLS:

{text}

RETURN ONLY VALID JSON IN THIS EXACT FORMAT:
{{
    "skills": [
        {{
            "name": "skill name",
            "category": "category name"
        }}
    ]
}}

RULES:
1. Use ONLY these categories: {", ".join(predefined_categories)}
2. If no category matches, use "Other"
3. Return empty array if no skills found
4. NEVER include markdown formatting
5. Return ONLY the JSON object, no other text
"""

    try:
        response = client.models.generate_content(
            model=model,
            contents=[prompt],
            config=types.GenerateContentConfig(
                temperature=0.1,  # More deterministic
                max_output_tokens=2000
            )
        )
        
        full_response = response.text.strip()
        print(f"🔍 Raw Gemini response: '{full_response}'")

        # Clean the response
        full_response = full_response.replace("```json", "").replace("```", "").strip()
        
        if not full_response:
            raise ValueError("Empty response from Gemini")
            
        # Parse JSON
        result = json.loads(full_response)
        
        # Validate structure
        if not isinstance(result, dict):
            raise ValueError("Response is not a JSON object")
        if "skills" not in result:
            result["skills"] = []
            
        return result
        
    except json.JSONDecodeError as e:
        print(f"⚠️ Failed to parse Gemini response as JSON: {e}")
        print(f"💬 Response was: '{full_response}'")
        return {"skills": [], "error": f"Invalid JSON: {str(e)}"}
    except Exception as e:
        print(f"⚠️ Gemini API error: {e}")
        return {"skills": [], "error": str(e)}

def extract_skills_from_file(path: str) -> dict:
    """Read a text file and extract skills using Gemini"""
    if not os.path.exists(path):
        print(f"❌ File not found: {path}")
        return {"skills": [], "error": "File not found"}

    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        return extract_skills_from_text(text)
    except Exception as e:
        print(f"⚠️ Failed to read file: {e}")
        return {"skills": [], "error": str(e)}

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python extract_skills.py <path_to_text_file>")
        sys.exit(1)

    path = sys.argv[1]
    result = extract_skills_from_file(path)
    print(json.dumps(result, indent=4, ensure_ascii=False))