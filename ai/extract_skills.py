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
    model = "gemini-2.5-pro"

    predefined_categories = get_predefined_categories()
    
    prompt = f"""
You are an expert at extracting skills from professional documents. 
Analyze the following text and extract skills in JSON format.

Required output format:
{{
    "skills": [
        {{
            "name": "skill name",
            "category": "category from predefined list"
        }}
    ],
    "business_id": "employee identifier if available"
}}

Rules:
1. Use ONLY these categories: {", ".join(predefined_categories)}
2. Never include empty skill names
3. Return only valid JSON (no markdown formatting)
4. If no skills found, return empty "skills" array

Text to analyze:
{text}
"""

    contents = [
        types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
    ]

    tools = [types.Tool(googleSearch=types.GoogleSearch())]
    config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_budget=-1),
        tools=tools,
    )

    full_response = ""
    try:
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=config,
        ):
            full_response += chunk.text
    except Exception as e:
        print(f"⚠️ Gemini API error: {e}")
        return {"skills": [], "error": str(e)}

    print("🔍 Raw Gemini response:")
    print(full_response)

    try:
        # Clean and parse response
        full_response = full_response.replace("```json", "").replace("```", "")
        result = json.loads(full_response)
        
        # Validate structure
        if not isinstance(result, dict):
            raise ValueError("Response is not a JSON object")
        if "skills" not in result:
            result["skills"] = []
            
        return result
    except Exception as e:
        print(f"⚠️ Failed to parse Gemini response: {e}")
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