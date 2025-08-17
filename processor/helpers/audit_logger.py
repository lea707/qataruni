from pathlib import Path
import json

def log_conversion(data, original_path):
    logs_dir = Path("profiles/logs")
    logs_dir.mkdir(exist_ok=True)

    base_name = Path(original_path).stem  
    log_path = logs_dir / f"{base_name}.json"

    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)