import os
import json
import sys
from pathlib import Path

# Get the current directory and add the ai module to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
module_dir = os.path.join(project_root, 'ai')
sys.path.append(module_dir)

from ai.employee_extractor import extract_employee_profile

# Paths
META_PATH = "meta.json"
JSON_OUTPUT_DIR = os.path.join("profiles", "jsons")

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

def save_json(result, txt_path):
    os.makedirs(JSON_OUTPUT_DIR, exist_ok=True)
    name = Path(txt_path).stem
    out_path = os.path.join(JSON_OUTPUT_DIR, f"{name}.json")
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=4, ensure_ascii=False)
        print(f"✅ Saved JSON to: {out_path}")
    except Exception as e:
        print(f"⚠️ Failed to save JSON: {e}")

def process_file(path: str):
    print(f"🧠 AIEmployeeProcessor working on: {path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        print(f"❌ File not found: {path}")
        return None

    result = extract_employee_profile(text)

    if result and isinstance(result, dict):
        return result
    else:
        print("⚠️ No valid dictionary returned from Gemini")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ai_employee_processor.py <path_to_txt_file>")
        sys.exit(1)

    file_path = sys.argv[1]
    result = process_file(file_path)

    if result:
        print(json.dumps(result, indent=4, ensure_ascii=False))
        save_json(result, file_path)

        # Optional: update meta
        meta = load_meta()
        meta[file_path] = {"processed_at": Path(file_path).stat().st_mtime}
        save_meta(meta)