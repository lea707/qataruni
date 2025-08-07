import os
import json
from google import genai
from google.genai import types

def extract_skills_from_text(text: str) -> dict:
    client = genai.Client(
        api_key="AIzaSyAjDLkmiUQnleseIXcZaSyrruxR6OP5RRY"
    )

    model = "gemini-2.5-pro"
    prompt = f"""
I need you to read this text extracted from a CV and produce output in JSON format.

It should contain:
- A list of skills mentioned in the CV
- A category for each skill (e.g. Technical Skills, Soft Skills, Programming Skills, Language Skills)

Return only the JSON object. No explanation, no markdown, no formatting.

Text:
{text}
"""

    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt)],
        )
    ]

    tools = [types.Tool(googleSearch=types.GoogleSearch())]

    generate_content_config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_budget=-1),
        tools=tools,
    )

    full_response = ""
    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        full_response += chunk.text

    # Optional: print raw response for debugging
    print("🔍 Raw Gemini response:")
    print(full_response)

    # Try to extract JSON block
    try:
        full_response    = full_response.replace("```json", "").replace("```", "")
        return json.loads(full_response)
    except Exception as e:
        print(f"⚠️ Failed to parse Gemini response: {e}")
        return {}

def extract_skills_from_file(path: str) -> dict:
    if not os.path.exists(path):
        print(f"❌ File not found: {path}")
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        return extract_skills_from_text(text)
    except Exception as e:
        print(f"⚠️ Failed to read file: {e}")
        return {}

if __name__ == "__main__":
    import sys
    result = extract_skills_from_file("employee_documents/abc-1/documents/cv.txt")
    print(json.dumps(result, indent=4, ensure_ascii=False))