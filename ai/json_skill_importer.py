import json
from pathlib import Path
from typing import Dict
from datetime import datetime
from database.connection import db
from models.employee import Employee
from models.skill import Skill
from models.skill_category import SkillCategory
from models.associations import employee_skills
from sqlalchemy import select, func
from sqlalchemy.orm.exc import MultipleResultsFound
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
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Debug: Print raw JSON
            print(f"RAW JSON CONTENT:\n{json.dumps(data, indent=2)}")
            
            # Enhanced validation
            if not isinstance(data, dict):
                raise ValueError("Top-level must be a dictionary")
                
            if "skills" not in data:
                raise ValueError("Missing 'skills' array")
                
            valid_skills = [
                s for s in data["skills"] 
                if isinstance(s, dict) and s.get("name", "").strip()
            ]
            
            if not valid_skills:
                raise ValueError(f"No valid skills in {len(data['skills'])} entries")
                
            # Process only valid skills
            data["skills"] = valid_skills
            return self._process_valid_file(json_path, data)
            
        except Exception as e:
            self._quarantine_file(json_path, str(e))
            raise
    
    def _archive_file(self, json_path: Path, business_id: str):
        """Copy file to processed directory with timestamp, preserving original"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        new_name = f"{business_id}_{timestamp}{json_path.suffix}"
        new_path = self.processed_dir / new_name

        try:
            shutil.copy2(json_path, new_path)
            print(f"[ARCHIVE] Copied to: {new_path}")
        except Exception as e:
            print(f"[ERROR] Failed to archive {json_path.name}: {e}")
 
    def _process_valid_file(self, json_path: Path, data: dict):
        """Process a validated JSON file with skills data"""
        session = db()
        try:
            business_id = data.get("business_id")
            if not business_id:
                raise ValueError("Missing business_id in JSON")
            
            # Find employee
            employee = session.scalars(
                select(Employee).where(Employee.busness_id == business_id)
            ).one_or_none()
            
            if not employee:
                raise ValueError(f"No employee found for business_id: {business_id}")
            
            print(f"👤 Processing skills for employee: {employee.english_name} (ID: {employee.emp_id})")
            
            # Process each skill - ONLY ADD NEW ONES
            skill_count = 0
            for skill_data in data["skills"]:
                try:
                    # Only add if association doesn't exist
                    skill_name = skill_data.get("name", "").strip()
                    if not skill_name:
                        continue
                        
                    # Check if skill already exists for employee
                    existing = session.scalars(
                        select(employee_skills)
                        .join(Skill)
                        .where(
                            (employee_skills.c.employee_id == employee.emp_id) &
                            (func.lower(Skill.skill_name) == func.lower(skill_name))
                        )
                    ).one_or_none()
                    
                    if not existing:
                        self._process_skill(session, employee.emp_id, skill_data)
                        skill_count += 1
                except Exception as e:
                    print(f"⚠️ Failed to process skill {skill_data.get('name')}: {str(e)}")
                    continue
            
            session.commit()
            print(f"✅ Added {skill_count} new skills (of {len(data['skills'])} total) for {business_id}")
            self._archive_file(json_path, business_id)
            
            return {
                "employee_id": employee.emp_id,
                "skills_added": skill_count,
                "total_skills_in_file": len(data["skills"])
            }
            
        except Exception as e:
            session.rollback()
            print(f"❌ Transaction failed: {str(e)}")
            self._quarantine_file(json_path, str(e))
            raise
        finally:
            session.close()
    
    def _quarantine_file(self, json_path: Path, error: str):
        # Save error copy
        debug_path = self.quarantine_dir / f"DEBUG_{json_path.name}"
        try:
            with open(json_path, 'r') as src, open(debug_path, 'w') as dst:
                dst.write(f"// ERROR: {error}\n")
                dst.write(src.read())
        except Exception as e:
            print(f"DEBUG SAVE FAILED: {e}")
    
    def _process_skill(self, session, employee_id: int, skill_data: Dict):
        """Process skill with robust category handling"""
        skill_name = skill_data.get("name", "").strip()
        category_name = skill_data.get("category", "").strip()
        
        if not skill_name:
            print(f"⚠️ Invalid skill (missing name): {skill_data}")
            return

        print(f"\n🔍 Processing: {skill_name} (Category: '{category_name}')")

        # 1. Handle Uncategorized Skills
        if not category_name:
            print("⚠️ No category specified - assigning to 'Uncategorized'")
            category_name = "Uncategorized"

        # 2. Case-Insensitive Category Lookup
        try:
            category = session.scalars(
                select(SkillCategory).where(
                    func.lower(SkillCategory.category_name) == func.lower(category_name)
                )
            ).one_or_none()
        except MultipleResultsFound as e:
            print(f"❌ ERROR: Multiple categories found for '{category_name}'. Using the first one.")
            category = session.scalars(
                select(SkillCategory).where(
                    func.lower(SkillCategory.category_name) == func.lower(category_name)
                )
            ).first()
        
        # 3. Create New Category if Needed
        if not category:
            print(f"➕ Creating NEW category: '{category_name}'")
            try:
                category = SkillCategory(category_name=category_name)
                session.add(category)
                session.flush()
                print(f"Created category ID: {category.category_id}")
            except Exception as e:
                # This fallback is what's causing your issue, so we'll log it clearly
                print(f"❌ Failed to create category '{category_name}': {e}")
                # Fallback to existing 'Uncategorized' category
                category = session.scalars(
                    select(SkillCategory).where(
                        func.lower(SkillCategory.category_name) == "uncategorized"
                    )
                ).one_or_none()
                if not category:
                    raise ValueError("Could not find or create category")
        
        # 4. Skill Processing
        skill = session.scalars(
            select(Skill).where(func.lower(Skill.skill_name) == func.lower(skill_name))
        ).one_or_none()

        if not skill:
            print(f"➕ Creating new skill: '{skill_name}'")
            skill = Skill(
                skill_name=skill_name,
                category_id=category.category_id
            )
            session.add(skill)
            session.flush()

        # 5. Create Association
        exists = session.scalars(
            select(employee_skills).where(
                (employee_skills.c.employee_id == employee_id) &
                (employee_skills.c.skill_id == skill.skill_id)
            )
        ).one_or_none()

        if not exists:
            print(f"🤝 Creating association for {skill_name}")
            session.execute(
                employee_skills.insert().values(
                    employee_id=employee_id,
                    skill_id=skill.skill_id,
                    certified=skill_data.get("certified", False),
                    skill_level=skill_data.get("level", "Not Specified")
                )
            )