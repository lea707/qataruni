import json
from pathlib import Path
from typing import Dict
from datetime import datetime
from database.connection import db
from models.employee import Employee
from models.skill import Skill
from models.skill_category import SkillCategory
from models.associations import employee_skills
from sqlalchemy import select
import shutil  

class JSONSkillImporter:
    def __init__(self):
        self.input_dir = Path("converted/json_files")
        self.processed_dir = Path("converted/json_processed")
        self.quarantine_dir = self.processed_dir / "quarantine"
        self.report_path = self.processed_dir / "quarantine_report.txt"
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)

    def process_all_files(self):
        """Process all JSON files from the input directory"""
        with open(self.report_path, "w", encoding="utf-8") as report:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            report.write(f"🧾 Quarantine Report — {now}\n\n")
        for json_file in self.input_dir.glob("*.json"):
            try:
                self.process_file(json_file)
            except ValueError as ve:
                msg = str(ve)
                if "Missing business_id" in msg:
                    print(f"[SKIP] {json_file.name}: {msg}")
                elif "Multiple rows were found" in msg:
                    print(f"[AMBIGUOUS] {json_file.name}: {msg}")
                else:
                    print(f"[ERROR] {json_file.name}: {msg}")
                    self._quarantine_file(json_file, msg)
            except Exception as e:
                print(f"[ERROR] {json_file.name}: {str(e)}")
                self._quarantine_file(json_file, str(e))

    def process_file(self, json_path: Path):
        """Process and archive a single JSON file"""
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, dict):
            raise ValueError("Invalid JSON format: Expected dictionary")

        business_id = data.get("business_id")
        if not business_id:
            raise ValueError("Missing business_id in JSON")

        skills = data.get("skills", [])
        if not skills:
            print(f"[INFO] No skills found in {json_path.name}")
            self._archive_file(json_path, business_id)
            return

        session = db()
        try:
            employee = session.scalars(
                select(Employee).where(Employee.busness_id == business_id)
            ).one_or_none()

            if not employee:
                print(f"[WARN] No employee found for busness_id: {business_id}")
                self._quarantine_file(json_path, f"No employee found for busness_id: {business_id}")
                return

            print(f"[DEBUG] Matched employee: {employee.emp_id} — {employee.english_name}")

            for skill_data in skills:
                self._process_skill(session, employee.emp_id, skill_data)

            session.commit()
            print(f"[SUCCESS] Processed {len(skills)} skills from {json_path.name}")
            self._archive_file(json_path, business_id)

        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
    def _process_skill(self, session, employee_id: int, skill_data: Dict):
        """Process individual skill entry"""
        skill_name = skill_data.get("skill", "").strip()
        category_name = skill_data.get("category", "").strip()

        if not skill_name:
            return

        category = session.execute(
            select(SkillCategory).where(SkillCategory.category_name.ilike(category_name))
        ).scalar_one_or_none()

        if not category and category_name:
            category = SkillCategory(category_name=category_name)
            session.add(category)
            session.flush()

        skill = session.execute(
            select(Skill).where(Skill.skill_name.ilike(skill_name))
        ).scalar_one_or_none()

        if not skill:
            skill = Skill(
                skill_name=skill_name,
                category_id=category.category_id if category else None
            )
            session.add(skill)
            session.flush()

        exists = session.execute(
            select(employee_skills).where(
                (employee_skills.c.employee_id == employee_id) &
                (employee_skills.c.skill_id == skill.skill_id)
            )
        ).scalar_one_or_none()

        if not exists:
            session.execute(
                employee_skills.insert().values(
                    employee_id=employee_id,
                    skill_id=skill.skill_id,
                    certified=skill_data.get("certified", False),
                    skill_level=skill_data.get("level")
                )
            )
    def _archive_file(self, json_path: Path, business_id: str):
        """Copy file to processed directory with timestamp, preserving original"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        new_name = f"{business_id}_{timestamp}{json_path.suffix}"
        new_path = self.processed_dir / new_name

        try:
            shutil.copy2(json_path, new_path)  # ✅ Copy instead of move
            print(f"[ARCHIVE] Copied to: {new_path}")
        except Exception as e:
            print(f"[ERROR] Failed to archive {json_path.name}: {e}")

    def _quarantine_file(self, json_path: Path, reason: str = "Unknown error"):
        """Log problematic file without moving it"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        error_tag = reason.split(":")[0].replace(" ", "_").replace("[", "").replace("]", "")
        new_name = f"{json_path.stem}_ERROR_{datetime.now().strftime('%Y%m%d_%H%M%S')}{json_path.suffix}"
        quarantine_path = self.quarantine_dir / new_name

        print(f"[QUARANTINE] Would quarantine: {json_path.name} → {quarantine_path.name} due to: {reason}")

        # Log to quarantine report
        with open(self.report_path, "a", encoding="utf-8") as report:
            report.write(f"File: {json_path.name}\n")
            report.write(f"Reason: {reason}\n")
            report.write(f"Suggested Action: Check format, structure, or database integrity\n")
            report.write(f"---\n")

        # Optional: remove empty quarantine folder
        if self.quarantine_dir.exists() and not any(self.quarantine_dir.iterdir()):
            try:
                self.quarantine_dir.rmdir()
                print(f"[CLEANUP] Removed empty quarantine folder")
            except Exception as e:
                print(f"[WARN] Could not remove quarantine folder: {e}")