from flask import current_app
from database.repositories.employee_repository import EmployeeRepository
from database.repositories.position_repository import PositionRepository
from database.repositories.skill_repository import SkillRepository
from datetime import datetime

from models.employee import Employee
from models.skill import Skill
class EmployeeService:
    def __init__(self):
        self.repository = EmployeeRepository()
        self.position_repository = PositionRepository()
        self.skill_repository = SkillRepository()

    def _prepare_employee_data(self, form_data):
        try:
            return {
                'english_name': form_data.get('english_name'),
                'arab_name': form_data.get('arab_name'),
                'email': form_data.get('email'),
                'phone': form_data.get('phone'),
                'position_id': int(form_data.get('position_id')),
                'department_id': int(form_data.get('department_id')),
                'level_id': int(form_data.get('level_id')),
                'hire_date': datetime.strptime(form_data.get('hire_date'), '%Y-%m-%d').date(),
                'supervisor_emp_id': int(form_data['supervisor_emp_id']) if form_data.get('supervisor_emp_id') else None,
                'busness_id': self.repository._generate_business_id()
            }
        except Exception as e:
            print(f"Error preparing employee data: {e}")
            raise

    def create_employee(self, form_data):
        try:
            employee_data = self._prepare_employee_data(form_data)
            return self.repository.create_employee(employee_data)
        except Exception as e:
            print(f"Service error: {e}")
            return False

    def _prepare_skills_data(self, form_data):
        """Handle both MultiDict and regular dict for skill data"""
        skills = []
        
        if hasattr(form_data, 'getlist'):
            skill_names = form_data.getlist('skill_name[]')
            skill_categories = form_data.getlist('skill_category[]')
            skill_levels = form_data.getlist('skill_level[]')
            
            skills = [{
                'name': name,
                'category': cat,
                'level': level
            } for name, cat, level in zip(skill_names, skill_categories, skill_levels)]
        else:
            if form_data.get('skill_name[]'):
                skills = [{
                    'name': form_data.get('skill_name[]'),
                    'category': form_data.get('skill_category[]'),
                    'level': form_data.get('skill_level[]')
                }]
        
        return skills
    def get_all_employees(self):
     return self.repository.get_all_employees()
    def get_employee(self, employee_id):
        """Get employee details by ID"""
        try:
            employee = self.repository.get_employee(employee_id)
            if not employee:
                raise ValueError("Employee not found")
            return employee
        except Exception as e:
            print(f"Error getting employee: {e}")
            raise

    def delete_employee(self, employee_id: int) -> bool:
     """Delete a employee by ID"""
     return self.repository.delete_employee(employee_id)
    from datetime import datetime
from models.employee import Employee
from database.repositories.employee_repository import EmployeeRepository
from flask import current_app

class EmployeeService:
    def __init__(self, db_session):
        self.db = db_session  # Store the database session
        self.repository = EmployeeRepository(db_session)

    def update_employee(self, employee_id: int, form_data: dict, files=None) -> bool:
        """
        Update an existing employee with all related data
        Args:
            employee_id: ID of employee to update
            form_data: Dictionary containing form data
            files: Optional file uploads for documents
        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            # Get existing employee
            employee = self.db.query(Employee).get(employee_id)
            if not employee:
                raise ValueError("Employee not found")

            # Update basic employee info
            employee.english_name = form_data.get('english_name', employee.english_name)
            employee.arab_name = form_data.get('arab_name', employee.arab_name)
            employee.email = form_data.get('email', employee.email)
            employee.phone = form_data.get('phone', employee.phone)
            
            if form_data.get('hire_date'):
                employee.hire_date = datetime.strptime(
                    form_data['hire_date'], '%Y-%m-%d'
                ).date()

            employee.position_id = int(form_data.get('position_id', employee.position_id))
            employee.department_id = int(form_data.get('department_id', employee.department_id))
            employee.level_id = int(form_data.get('level_id', employee.level_id))
            employee.supervisor_emp_id = (
                int(form_data['supervisor_emp_id']) 
                if form_data.get('supervisor_emp_id') 
                else None
            )
            employee.is_active = form_data.get('is_active', str(employee.is_active)).lower() == 'true'
            employee.updated_at = datetime.utcnow()

            # Process skills if provided
            if 'skill_ids[]' in form_data or 'skill_ids' in form_data:
                skill_ids = (
                    form_data.getlist('skill_ids[]') 
                    if hasattr(form_data, 'getlist') 
                    else form_data.get('skill_ids', '').split(',')
                )
                self._process_employee_skills(employee_id, skill_ids)

            # Commit changes to employee first
            self.db.commit()

            # Process documents if files were uploaded
            if files and 'document_files[]' in files:
                from services.employee_document_service import EmployeeDocumentService
                doc_service = EmployeeDocumentService(self.db)  # Pass the same session
                doc_service.save_employee_documents(
                    employee_id=employee_id,
                    form_data=form_data,
                    files=files
                )

            return True

        except ValueError as ve:
            self.db.rollback()
            current_app.logger.error(f"Validation error updating employee: {ve}")
            raise ve
        except Exception as e:
            self.db.rollback()
            current_app.logger.error(f"Error updating employee {employee_id}: {e}")
            raise RuntimeError(f"Failed to update employee: {e}")

    def _process_employee_skills(self, employee_id: int, skill_ids) -> None:
        """Helper method to process skill associations"""
        employee = self.db.query(Employee).get(employee_id)
        if not employee:
            raise ValueError("Employee not found")

        # Clear existing skills
        employee.skills = []

        # Handle both array and comma-separated formats
        if isinstance(skill_ids, str):
            skill_ids = [int(id.strip()) for id in skill_ids.split(',') if id.strip()]
        elif isinstance(skill_ids, list):
            skill_ids = [int(id) for id in skill_ids if id]

        # Add validated skills
        for skill_id in skill_ids:
            skill = self.db.query(Skill).get(skill_id)
            if skill:
                employee.skills.append(skill)