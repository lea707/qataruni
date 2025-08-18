from database.repositories.skill_repository import SkillRepository
from database.repositories.skill_category_repository import SkillCategoryRepository
from models.employee import Employee
from models.skill import Skill
from models.skill_category import SkillCategory
from models.associations import employee_skills
from database.connection import db  # Import the global session
from sqlalchemy import select, and_
import json
from pathlib import Path
from typing import Dict, List
from flask import current_app
from sqlalchemy.orm import joinedload
from database.repositories.skill_repository import SkillRepository
from database.repositories.skill_category_repository import SkillCategoryRepository
from models.skill import Skill
from models.skill_category import SkillCategory
from database.connection import db  # This imports your SessionLocal instance
from sqlalchemy.orm import joinedload
from flask import current_app


class SkillService:
    def __init__(self):
        self.repository = SkillRepository()
        self.category_repository = SkillCategoryRepository()
        self.all_skills = self.repository.get_all_skills()
        from database.connection import db
        self.db = db() 
    def get_all_skills_serializable(self, include_category=False):
        try:
            query = self.db.query(Skill)  # Use the session directly
            
            if include_category:
                query = query.options(joinedload(Skill.category))
                
            skills = query.all()
            
            return [{
                'skill_id': s.skill_id,
                'skill_name': s.skill_name,
                'category': s.category.category_name if include_category and s.category else None
            } for s in skills]
        except Exception as e:
            current_app.logger.error(f"Error getting skills: {str(e)}")
            return []
        finally:
            self.db.close()
    def get_skills_by_employee(self, employee_id):
        return self.repository.get_skills_by_employee(employee_id)

    def get_all_skill_categories(self):
        return self.category_repository.get_all_categories()

    def get_all_skill_levels(self):
        session = self.db() if callable(self.db) else self.db
        try:
            return self.repository.get_distinct_skill_levels(session)
        finally:
            if callable(self.db):
                session.close()

    def get_all_skills(self):
        return self.repository.get_all_skills()

    def search_skills(self, query):
        """Search skills by name (case-insensitive partial match)"""
        return self.repository.search_skills(query)

    def process_json_directory(self, folder_path: str = "converted/json") -> Dict[str, int]:
        """Process all JSON files in a directory"""
        json_folder = Path(folder_path)
        if not json_folder.exists():
            raise FileNotFoundError(f"JSON folder not found: {folder_path}")

        results = {
            'files_processed': 0,
            'total_skills': 0,
            'employees_not_found': [],
            'errors': []
        }

        for json_file in json_folder.glob('*.json'):
            try:
                file_results = self.import_skills_from_json_file(str(json_file))
                results['files_processed'] += 1
                results['total_skills'] += file_results['skills_added']
                if file_results['employee_found'] is False:
                    results['employees_not_found'].append(json_file.name)
            except Exception as e:
                results['errors'].append(f"{json_file.name}: {str(e)}")
                continue

        return results

    
    def _import_skills_data(self, json_data: Dict) -> Dict[str, int]:
        """Internal method to process skill data"""
        session = self.db() if callable(self.db) else self.db
        results = {
            'skills_added': 0,
            'employee_found': True,
            'categories_created': 0
        }

        try:
            business_id = json_data.get('business_id')
            if not business_id:
                raise ValueError("Missing business_id in JSON data")

            employee = session.execute(
                select(Employee).where(Employee.busness_id == business_id)
            ).scalar_one_or_none()

            if not employee:
                results['employee_found'] = False
                return results

            for skill_data in json_data.get('skills', []):
                skill_name = skill_data.get('skill', '').strip()
                if not skill_name:
                    continue

                # Process category
                category_name = skill_data.get('category', '').strip()
                category = None
                if category_name:
                    category = session.execute(
                        select(SkillCategory)
                        .where(SkillCategory.category_name.ilike(category_name))
                    ).scalar_one_or_none()
                    if not category:
                        category = SkillCategory(category_name=category_name)
                        session.add(category)
                        session.flush()
                        results['categories_created'] += 1

                # Process skill
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

                # Create association if not exists
                if not session.execute(
                    select(employee_skills)
                    .where(
                        (employee_skills.c.employee_id == employee.emp_id) &
                        (employee_skills.c.skill_id == skill.skill_id))
                ).scalar_one_or_none():
                    session.execute(
                        employee_skills.insert().values(
                            employee_id=employee.emp_id,
                            skill_id=skill.skill_id,
                            skill_level=skill_data.get('level'),
                            certified=skill_data.get('certified', False)
                        )
                    )
                    results['skills_added'] += 1

            session.commit()
            return results

        except Exception as e:
            session.rollback()
            raise RuntimeError(f"Failed to import skills: {str(e)}")
        finally:
            if callable(self.db):
                session.close()