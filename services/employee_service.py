#
# This file contains the core business logic for managing employees,
# including create, read, update, and delete operations.
#
from sqlalchemy import text
import uuid
import json
import os
from pathlib import Path
from sqlalchemy.orm import joinedload, aliased
from flask import current_app
from datetime import datetime
from werkzeug.utils import secure_filename
from sqlalchemy import text, select
from sqlalchemy.orm import joinedload
from database.repositories.employee_repository import EmployeeRepository
from database.repositories.position_repository import PositionRepository
from database.repositories.skill_repository import SkillRepository
from database.connection import db
from models.department import Department
from models.employee import Employee
from models.skill import Skill
from models.skill_category import SkillCategory
from models.employee_document import EmployeeDocument
from models.certificate_type import CertificateType
from models.document_type import DocumentType
from models.associations import employee_skills
from processor.employee_processor import EmployeeDocumentProcessor
from services.file_handler import handle_file_uploads # Import the new file handler service

class EmployeeService:
    def __init__(self, db_session=None):
        self.db = db_session if db_session is not None else db
        self.repository = EmployeeRepository()

    def _process_json_skills(self, employee_id: int, business_id: str, session):
        """Process skills from JSON file (now uses converted/json_files)"""
        json_path = Path("converted/json_files") / f"{business_id}.json"
        if not json_path.exists():
            current_app.logger.debug(f"No JSON file found at {json_path}")
            return
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Assuming 'skills' is a key in the JSON structure
            skills_data = data.get('skills', {})
            
            for skill_category_name, skill_list in skills_data.items():
                for skill_name in skill_list:
                    # Retrieve or create skill and skill category
                    skill_category = session.query(SkillCategory).filter_by(category_name=skill_category_name).first()
                    if not skill_category:
                        skill_category = SkillCategory(category_name=skill_category_name)
                        session.add(skill_category)
                        session.commit()
                    
                    skill = session.query(Skill).filter_by(skill_name=skill_name).first()
                    if not skill:
                        skill = Skill(skill_name=skill_name, category_id=skill_category.category_id)
                        session.add(skill)
                        session.commit()

                    # Link skill to employee
                    employee = session.query(Employee).get(employee_id)
                    if employee and skill not in employee.skills:
                        employee.skills.append(skill)
                        session.commit()
                        
        except Exception as e:
            current_app.logger.error(f"Failed to process skills from JSON for employee {business_id}: {e}")

    def update_employee(self, employee_id: int, form_data, files=None):
        """
        Updates an existing employee's details and handles new skill and document uploads.
        
        Args:
            employee_id: The ID of the employee to update.
            form_data: The form data from the POST request.
            files: The files dictionary from the POST request (request.files).
        """
        session = self.db() if callable(self.db) else self.db
        
        # --- DEBUGGING PRINTS START ---
        print("\n--- DEBUG: Incoming Update Data ---")
        print(f"Employee ID: {employee_id}")
        print(f"Form Data Keys: {form_data.keys()}")
        print(f"Files Keys: {files.keys()}")
        print("------------------------------------\n")
        # --- DEBUGGING PRINTS END ---

        try:
            employee = session.query(Employee).filter_by(emp_id=employee_id).first()
            if not employee:
                current_app.logger.warning(f"Employee with ID {employee_id} not found for update.")
                return False

            # Update core employee fields from form data
            employee.english_name = form_data.get('english_name', employee.english_name)
            employee.arab_name = form_data.get('arab_name', employee.arab_name)
            employee.busness_id = form_data.get('business_id', employee.busness_id)
            employee.email = form_data.get('email', employee.email)
            employee.phone = form_data.get('phone', employee.phone)
            
            # Check for and handle hire_date update
            hire_date_str = form_data.get('hire_date')
            if hire_date_str:
                try:
                    employee.hire_date = datetime.strptime(hire_date_str, '%Y-%m-%d').date()
                except ValueError as e:
                    current_app.logger.error(f"Invalid hire_date format: {hire_date_str}. Error: {e}")
            
            employee.department_id = form_data.get('department_id', employee.department_id)
            employee.position_id = form_data.get('position_id', employee.position_id)
            employee.level_id = form_data.get('level_id', employee.level_id)
            employee.supervisor_emp_id = form_data.get('supervisor_emp_id') if form_data.get('supervisor_emp_id') else None
            employee.is_active = 'is_active' in form_data
            
            # ==================== SKILLS UPDATE LOGIC ====================
            # Clear all existing skills to handle removals and updates
            employee.skills.clear()
            
            # Process and add existing skills (from the original form)
            # This assumes the skills select box sends skill IDs
            selected_skills = form_data.getlist('skills[]')
            for skill_id in selected_skills:
                skill = session.query(Skill).get(skill_id)
                if skill:
                    employee.skills.append(skill)
            
            # Process and add new skills (from the dynamically added hidden inputs)
            new_skills_json = form_data.getlist('new_skills[]')
            for skill_json in new_skills_json:
                try:
                    skill_data = json.loads(skill_json)
                    skill_name = skill_data.get('name')
                    skill_level = skill_data.get('level')
                    skill_category_id = skill_data.get('category_id')
                    
                    # Check if skill already exists in the database
                    skill = session.query(Skill).filter_by(skill_name=skill_name).first()
                    if not skill:
                        # Create a new skill if it doesn't exist
                        skill = Skill(skill_name=skill_name, category_id=skill_category_id)
                        session.add(skill)
                        session.flush() # Flush to get the new skill ID
                    
                    # Link the skill to the employee with level and certification status
                    employee.skills.append(skill)
                    
                except json.JSONDecodeError as e:
                    current_app.logger.error(f"Failed to decode skill JSON: {e}")
            
            # ==================== DOCUMENTS UPDATE LOGIC ====================
            # Handle file uploads for new documents
            if files:
                current_app.logger.info(f"Processing file uploads for employee {employee_id}")
                current_app.logger.info(f"Files received: {list(files.keys())}")
                try:
                    # Use the file_handler service to save the files
                    handle_file_uploads(session, employee_id, files, form_data)
                    current_app.logger.info(f"Successfully processed file uploads for employee {employee_id}")
                except Exception as e:
                    current_app.logger.error(f"Error processing file uploads for employee {employee_id}: {e}")
                    # Don't fail the entire update if file upload fails
            
            session.commit()
            print(f"✅ Successfully updated employee with ID {employee_id}")
            return True

        except Exception as e:
            session.rollback()
            current_app.logger.error(f"Failed to update employee {employee_id}: {e}")
            print(f"❌ Failed to update employee with ID {employee_id}")
            return False

        finally:
            if callable(self.db):
                session.close()

    def create_employee(self, form_data, files=None):
        session = self.db() if callable(self.db) else self.db
        temp_files = []
        try:
            # Create a new employee object
            new_employee = Employee(
                english_name=form_data['english_name'],
                arab_name=form_data['arab_name'],
                busness_id=form_data['business_id'],
                email=form_data.get('email'),
                phone=form_data.get('phone'),
                # The 'address' field is not supported in the Employee model.
                # Remove this to avoid the same error on create.
                # address=form_data.get('address'),
                hire_date=datetime.strptime(form_data['hire_date'], '%Y-%m-%d').date(),
                department_id=form_data.get('department_id'),
                position_id=form_data.get('position_id'),
                level_id=form_data.get('level_id'),
                supervisor_emp_id=form_data.get('supervisor_emp_id') if form_data.get('supervisor_emp_id') else None
            )

            session.add(new_employee)
            session.flush() # Use flush to get the new emp_id before commit

            # Handle file uploads if they exist
            if files:
                handle_file_uploads(session, new_employee.emp_id, files, form_data)

            session.commit()
            return new_employee.emp_id
            
        except Exception as e:
            session.rollback()
            current_app.logger.error(f"Error creating new employee: {e}")
            raise RuntimeError(f"Could not create new employee: {e}")
        finally:
            if callable(self.db):
                session.close()

    def delete_employee(self, employee_id):
        session = self.db() if callable(self.db) else self.db
        try:
            employee = session.query(Employee).filter_by(emp_id=employee_id).first()
            if not employee:
                return False
            session.delete(employee)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            current_app.logger.error(f"Error deleting employee {employee_id}: {e}")
            return False
        finally:
            if callable(self.db):
                session.close()

    def get_all_employees(self):
        session = self.db() if callable(self.db) else self.db
        try:
            employees = session.query(Employee).options(joinedload(Employee.department), joinedload(Employee.position)).all()
            return employees
        finally:
            if callable(self.db):
                session.close()

    def get_employee(self, employee_id):
        session = self.db() if callable(self.db) else self.db
        try:
            employee = session.query(Employee).options(
                joinedload(Employee.department),
                joinedload(Employee.position),
                joinedload(Employee.level),
                joinedload(Employee.supervisor),
                joinedload(Employee.skills).joinedload(Skill.category),
                joinedload(Employee.documents).joinedload(EmployeeDocument.document_type),
                joinedload(Employee.documents).joinedload(EmployeeDocument.certificate_type)
            ).filter(Employee.emp_id == employee_id).first()
            return employee
        finally:
            if callable(self.db):
                session.close()
    
    def get_employee_by_business_id(self, business_id):
        session = self.db() if callable(self.db) else self.db
        try:
            employee = session.query(Employee).filter_by(busness_id=business_id).first()
            return employee
        finally:
            if callable(self.db):
                session.close()
    
    def business_id_exists(self, business_id):
        session = self.db() if callable(self.db) else self.db
        try:
            return session.query(Employee).filter_by(busness_id=business_id).first() is not None
        finally:
            if callable(self.db):
                session.close()

    def search_supervisors(self, query):
        session = self.db() if callable(self.db) else self.db
        try:
            search_pattern = f'%{query}%'
            # Supervisors must have at least one employee reporting to them
            supervisors = session.query(Employee).filter(
                (Employee.english_name.ilike(search_pattern) | Employee.busness_id.ilike(search_pattern))
            ).distinct().all()
            return supervisors
        finally:
            if callable(self.db):
                session.close()

   

    def get_employee_skills_with_metadata(self, employee_id):
        try:
            # Handle both direct session and sessionmaker cases
            session = self.db() if callable(self.db) else self.db
            
            result = session.execute(text("""
                SELECT s.skill_name, sc.category_name, 
                    es.skill_level, es.certified
                FROM employee_skills es
                JOIN skills s ON es.skill_id = s.skill_id
                LEFT JOIN skill_categories sc ON s.category_id = sc.category_id
                WHERE es.employee_id = :employee_id
                ORDER BY sc.category_name, s.skill_name
            """), {'employee_id': employee_id})
            
            return [
                (row.skill_name, 
                row.category_name or 'Uncategorized',
                row.skill_level if row.skill_level != 'Not Specified' else None,
                bool(row.certified))
                for row in result
            ]
        except Exception as e:
            current_app.logger.error(f"Error fetching skills: {str(e)}")
            return []
        finally:
            if callable(self.db) and 'session' in locals():
             session.close()

    def search_employees(self, **filters):
        session = self.db() if callable(self.db) else self.db
        try:
            query = session.query(Employee).options(
                joinedload(Employee.department), 
                joinedload(Employee.skills).joinedload(Skill.category),
                joinedload(Employee.position)
            )

            # Basic filters
            if filters.get('business_id'):
                query = query.filter(Employee.busness_id == filters['business_id'])
            if filters.get('name'):
                search_name = f"%{filters['name']}%"
                query = query.filter(
                    (Employee.english_name.ilike(search_name)) | 
                    (Employee.arab_name.ilike(search_name))
                )
                
            # Department filter - handle both ID and name cases
            if filters.get('department'):
                try:
                    # Try to convert to integer (if department_id was passed)
                    department_id = int(filters['department'])
                    query = query.filter(Employee.department_id == department_id)
                except ValueError:
                    # If conversion fails, assume it's a department name
                    query = query.join(Department).filter(
                        Department.department_name.ilike(f"%{filters['department']}%")
                    )

            # Position filter
            if filters.get('position_id'):
                query = query.filter(Employee.position_id == filters['position_id'])

            # Skill-related filters
            if filters.get('skill_name'):
                query = query.join(Employee.skills).filter(
                    Skill.skill_name.ilike(f"%{filters['skill_name']}%")
                )
            if filters.get('skill_category'):
                query = query.join(Employee.skills).join(Skill.category).filter(
                    SkillCategory.category_id == filters['skill_category']
                )

            # Document-related filters
            if filters.get('certificate_type'):
                query = query.join(Employee.documents).filter(
                    EmployeeDocument.certificate_type_id == filters['certificate_type']
                )
            if filters.get('document_type'):
                query = query.join(Employee.documents).filter(
                    EmployeeDocument.doc_type_id == filters['document_type']
                )

            # Supervisor filter
            if filters.get('supervisor_emp_id'):
                query = query.filter(Employee.supervisor_emp_id == filters['supervisor_emp_id'])

            # Date range filters
            if filters.get('hire_date_from'):
                try:
                    hire_date_from = datetime.strptime(filters['hire_date_from'], '%Y-%m-%d').date()
                    query = query.filter(Employee.hire_date >= hire_date_from)
                except ValueError:
                    pass
            if filters.get('hire_date_to'):
                try:
                    hire_date_to = datetime.strptime(filters['hire_date_to'], '%Y-%m-%d').date()
                    query = query.filter(Employee.hire_date <= hire_date_to)
                except ValueError:
                    pass

            # Sorting
            sort_by = filters.get('sort_by', 'name_asc')
            if sort_by == 'name_asc':
                query = query.order_by(Employee.english_name.asc())
            elif sort_by == 'name_desc':
                query = query.order_by(Employee.english_name.desc())
            elif sort_by == 'id_asc':
                query = query.order_by(Employee.busness_id.asc())
            elif sort_by == 'id_desc':
                query = query.order_by(Employee.busness_id.desc())
            elif sort_by == 'hiredate_asc':
                query = query.order_by(Employee.hire_date.asc())
            elif sort_by == 'hiredate_desc':
                query = query.order_by(Employee.hire_date.desc())

            employees = query.distinct().all()

            # Format results
            result = []
            for emp in employees:
                # Get skills with their levels from the association table
                emp_skills = session.query(
                    Skill.skill_name,
                    employee_skills.c.skill_level,
                    employee_skills.c.certified
                ).join(
                    employee_skills,
                    Skill.skill_id == employee_skills.c.skill_id
                ).filter(
                    employee_skills.c.employee_id == emp.emp_id
                ).all()

                result.append({
                    'id': emp.emp_id,
                    'emp_id': emp.emp_id,
                    'business_id': emp.busness_id,
                    'name': f"{emp.english_name} ({emp.arab_name})",
                    'department': emp.department.department_name if emp.department else '',
                    'position': emp.position.position_name if emp.position else '',
                    'supervisor_emp_id': emp.supervisor_emp_id,
                    'skills': {
                        'Technical': [
                            {
                                'name': s.skill_name,
                                'level': s.skill_level,
                                'certified': s.certified
                            } 
                            for s in emp_skills
                        ],
                    }
                })
            return result
        finally:
            if callable(self.db):
                session.close()