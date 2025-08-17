import os
import json
import re
from typing import Dict
from google import genai
from google.genai import types

def extract_employee_profile(text: str) -> dict:
    """
    Parses arbitrary employee-related text using Gemini and returns structured employee data.
    Handles CVs, HR notes, file paths, department info, and more.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("❌ GEMINI_API_KEY not set in environment.")

    client = genai.Client(api_key=api_key)
    model = "gemini-2.5-pro"

    prompt = f"""
You are an expert in parsing employee-related documents. Read the following text and extract structured information about each employee mentioned.

Return a JSON object with a list of employees. For each employee, include any of the following fields if available:
- full_name
- email
- phone_number
- department
- position
- skills: list of {{ name, category }}
- documents: list of file paths or filenames
- notes: any additional context or comments

Only return the JSON object. No explanation, no formatting.

Text:
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
        return {}

    print("🔍 Raw Gemini response:")
    print(full_response)

    try:
        full_response = full_response.replace("```json", "").replace("```", "")
        return json.loads(full_response)
    except Exception as e:
        print(f"⚠️ Failed to parse Gemini response: {e}")
        return {}

def extract_employee_profile_from_file(path: str) -> dict:
    """
    Reads a text file and extracts employee data using Gemini.
    """
    if not os.path.exists(path):
        print(f"❌ File not found: {path}")
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        return extract_employee_profile(text)
    except Exception as e:
        print(f"⚠️ Failed to read file: {e}")
        return {}


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python employee_extractor.py <path_to_text_file>")
        sys.exit(1)

    path = sys.argv[1]
    result = extract_employee_profile_from_file(path)
    print(json.dumps(result, indent=4, ensure_ascii=False))

def extract_metadata_from_notes(notes: str) -> Dict:
    result = {}
    if not notes:
        return result

    # Extract Business ID
    match = re.search(r"Business ID:\s*(\S+)", notes)
    if match:
        result["business_id"] = match.group(1)

    # Extract Arabic Name
    match = re.search(r"Arabic Name:\s*([^,]+)", notes)
    if match:
        result["arabic_name"] = match.group(1).strip()

    # Extract Is Active
    match = re.search(r"Is Active:\s*(yes|no)", notes, re.IGNORECASE)
    if match:
        result["is_active"] = match.group(1).lower() == "yes"

    return result
