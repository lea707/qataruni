import os
import json
import sys
from pathlib import Path

# Get the current directory and add the ai module to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
module_dir = os.path.join(project_root, 'ai')
sys.path.append(module_dir)

from ai.extract_skills import extract_skills_from_text

META_PATH = "meta.json"
JSON_OUTPUT_DIR = os.path.join("converted", "json_files")

def load_meta():
    if os.path.exists(META_PATH):
        try:
            with open(META_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Failed to load meta: {e}")
    return {}

def save_meta(data):
    try:
        with open(META_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Failed to save meta: {e}")

# ai_processor.py - update process_file function
def process_file(path: str):
    print(f"🧠 AIProcessor working on: {path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
            
        # Check if text is meaningful
        if len(text.strip()) < 50:
            print("⚠️ Text content too short for meaningful analysis")
            return {"skills": [], "business_id": os.path.basename(path).split('_')[0]}
            
    except FileNotFoundError:
        print(f"❌ File not found: {path}")
        return None

    result = extract_skills_from_text(text)
    
    # Debug logging
    print(f"🔍 AI result type: {type(result)}, content: {result}")
    
    if result and isinstance(result, dict):
        # Ensure we always have a skills array
        if "skills" not in result:
            result["skills"] = []
        return result
    else:
        print("⚠️ No valid dictionary returned from Gemini")
        return {"skills": [], "error": "Invalid response from AI"}



if __name__ == "__main__":
    process_file("employee_documents/abc-1/documents/cv.txt")