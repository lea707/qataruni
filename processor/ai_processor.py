import os
import json
import sys
module_dir = os.path.abspath('C:/Users/lea/OneDrive/Desktop/internship/qataruni/employee_tracker/ai')

# Add the directory to sys.path
sys.path.append(module_dir)

# Now you can import your module as usual
#import your_module


from ai.extract_skills import extract_skills_from_text

META_PATH = "meta.json"

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

def process_file(path: str):
    print(f"🧠 AIProcessor working on: {path}")

    # Load metadata
    meta = load_meta()

    # Check if file already processed
    if path in meta.get("processed", []):
        print(f"⏩ Already processed: {path}")
        return

    # Read the converted .txt file
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        print(f"❌ File not found: {path}")
        return

    # Send text to Gemini via extract_skills
    result = extract_skills_from_text(text)

    # Save the result as a JSON file
    if result and isinstance(result, dict):
        save_path = os.path.splitext(path)[0] + "_skills.json"
        try:
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=4, ensure_ascii=False)
            print(f"✅ Saved AI output to: {save_path}")

            # Update metadata
            meta.setdefault("processed", []).append(path)
            save_meta(meta)

        except Exception as e:
            print(f"❌ Failed to save output: {e}")
    else:
        print("⚠️ No valid dictionary returned from Gemini")

#add main method here
if __name__ == "__main__":
    process_file("employee_documents/abc-1/documents/cv.txt")

