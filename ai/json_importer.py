import json
import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict
import re
from sqlalchemy import select, and_
from ai.json_skill_importer import JSONSkillImporter
from database.connection import db

from models.employee import Employee
from models.department import Department
from models.skill import Skill
from models.skill_category import SkillCategory
from models.associations import employee_skills
class JSONImporter:
    def __init__(self):
        self.json_dir = Path("profiles/jsons")
        self.meta_path = Path("profiles/json_meta_data.json")
        self.json_dir.mkdir(parents=True, exist_ok=True)

    def get_json_files(self):
        return list(self.json_dir.glob("*.json"))

    def load_metadata(self):
        if not self.meta_path.exists():
            return {}

        try:
            with open(self.meta_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Failed to load metadata: {e}")
            return {}

    def save_metadata(self, data):
        try:
            with open(self.meta_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Failed to save metadata: {e}")

    def get_unprocessed_files(self):
        files = self.get_json_files()
        metadata = self.load_metadata()
        unprocessed = []

        for file in files:
            filename = file.name
            current_mtime = os.path.getmtime(file)

            if filename not in metadata or metadata[filename] != current_mtime:
                unprocessed.append(file)

        return unprocessed
    def process_all(self):
        metadata = self.load_metadata()
        unprocessed_files = self.get_unprocessed_files()

        if not unprocessed_files:
            print("⏸️ No new or changed files to process.")
            return

        for file in unprocessed_files:
            try:
                print(f"🔍 Processing: {file.name}")
                self.process_file(file) 
                metadata[file.name] = os.path.getmtime(file)
            except Exception as e:
                print(f"⚠️ Failed to process {file.name}: {e}")
        self.save_metadata(metadata)
        print("✅ Metadata updated.")

    def process_file(self, file: Path):
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)

        if "business_id" in data and "skills" in data and len(data.keys()) <= 3:
            print(f"📎 Detected skill-only update: {file.name}")
            copied_path = self.copy_to_skill_importer_dir(file)
            if copied_path:
                skill_importer = JSONSkillImporter()
                skill_importer.process_file(copied_path)
            return
        
        if "employees" in data and isinstance(data["employees"], list):
            print(f"👥 Detected multiple employees in: {file.name}")
            for emp_data in data["employees"]:
                self._process_employee(emp_data)
            return

        if "business_id" in data:
            print(f"👤 Detected full profile: {file.name}")
            self._process_employee(data)
            return

        raise ValueError(f"Unknown JSON structure in {file.name}")
    
    def _process_employee(self, data: Dict):
        required_fields = ["business_id", "english_name"]
        for field in required_fields:
            if not data.get(field):
                raise ValueError(f"Missing required field: {field}")

        session = db()
        try:
       
            employee = self._create_or_get_employee(data, session)

            for dept_info in data.get("departments", []):
             
                if isinstance(dept_info, str):
                    dept_name = dept_info.strip()
                    is_director = False
                    parent_name = None
                elif isinstance(dept_info, dict):
                    dept_name = dept_info.get("name", "").strip()
                    is_director = dept_info.get("is_director", False)
                    parent_name = dept_info.get("parent", "").strip()
                else:
                    continue

                if not dept_name:
                    continue

                department = self._create_or_get_department(dept_name, session)

                employee.department_id = department.department_id

                if is_director:
                    department.director_emp_id = employee.emp_id

                if parent_name:
                    parent_dept = self._create_or_get_department(parent_name, session)
                    department.parent_department_id = parent_dept.department_id

            for skill_data in data.get("skills", []):
                self._process_skill(session, employee.emp_id, skill_data)

            session.commit()
            print(f"✅ Finished processing employee: {employee.emp_id}")

        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
        notes_data = self._extract_metadata_from_notes(data.get("notes", ""))
        data.update(notes_data)

    def _extract_metadata_from_notes(self, notes: str) -> Dict:
        result = {}
        if not notes:
            return result

        match = re.search(r"Business ID:\s*(\S+)", notes)
        if match:
            result["business_id"] = match.group(1)

        match = re.search(r"Arabic Name:\s*([^,]+)", notes)
        if match:
            result["arabic_name"] = match.group(1).strip()

        match = re.search(r"Is Active:\s*(yes|no)", notes, re.IGNORECASE)
        if match:
            result["is_active"] = match.group(1).lower() == "yes"

        return result

    def copy_to_skill_importer_dir(self, file: Path):
        target_dir = Path("converted/json_files")
        target_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        new_name = f"{file.stem}_{timestamp}{file.suffix}"
        target_path = target_dir / new_name

        try:
            shutil.copy2(file, target_path)
            print(f"📁 Copied to skill importer dir: {target_path.name}")
            return target_path
        except Exception as e:
            print(f"⚠️ Failed to copy {file.name} to skill importer dir: {e}")
            return None