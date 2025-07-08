from flask import current_app, session
from database.repositories.employee_repository import EmployeeRepository
from database.repositories.position_repository import PositionRepository
from database.repositories.skill_repository import SkillRepository
from datetime import datetime
from database.connection import db
from models import skill
from models.employee import Employee
from models.skill import Skill
from sqlalchemy import text
from models.associations import employee_skills

class EmployeeService:
    def __init__(self, db_session=None):
        self.db = db_session if db_session is not None else db
        self.repository = EmployeeRepository()

    def _prepare_employee_data(self, form_data, session):
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
                'busness_id': self.repository._generate_business_id(session),
                'is_active': True,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
        except Exception as e:
            current_app.logger.error(f"Error preparing employee data: {e}")
            raise

    def create_employee(self, form_data, files=None):
        from models.associations import employee_skills

        if callable(self.db):
          session = self.db()  # It's a factory, create a session
        else:
            session = self.db  # It's already a session
        try:
            employee_data = self._prepare_employee_data(form_data, session)
            employee = Employee(**employee_data)
            session.add(employee)
            session.flush()  # Get employee.emp_id

            # Process skills
            skill_names = form_data.getlist('skill_name[]')
            skill_categories = form_data.getlist('skill_category[]')
            skill_levels = form_data.getlist('skill_level[]')

            for name, category, level in zip(skill_names, skill_categories, skill_levels):
                name = name.strip()
                if not name:
                    continue

                # Check if skill exists
                skill = session.query(Skill).filter_by(skill_name=name).first()
                if not skill:
                    skill = Skill(
                        skill_name=name,
                        category_id=int(category) if category and category != "select category" else None
                    )
                    session.add(skill)
                    session.flush()

                # Insert into association table with metadata
                session.execute(employee_skills.insert().values(
                    employee_id=employee.emp_id,
                    skill_id=skill.skill_id,
                    skill_level=level if level and level != "select level" else None
                ))

            from services.employee_document_service import EmployeeDocumentService
            doc_service = EmployeeDocumentService(session)
            doc_service.save_employee_documents(
                employee_id=employee.emp_id,
                form_data=form_data,
                files=files
            )

            session.commit()
            return employee.emp_id

        except Exception as e:
            session.rollback()
            current_app.logger.error(f"Error creating employee: {e}")
            raise RuntimeError(f"Failed to create employee: {str(e)}")
        finally:
            session.close()
  
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
            current_app.logger.error(f"Error getting employee: {e}")
            raise

    def delete_employee(self, employee_id: int) -> bool:
        """Delete a employee by ID"""
        return self.repository.delete_employee(employee_id)

    def update_employee(self, employee_id: int, form_data: dict, files=None) -> bool:
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
            if 'skill_name[]' in form_data:
                self._process_employee_skills(form_data, employee_id)

            # Commit changes to employee first
            self.db.commit()

            # Process documents if files were uploaded
            if files and 'document_files[]' in files:
                from services.employee_document_service import EmployeeDocumentService
                doc_service = EmployeeDocumentService(self.db)
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

    def _process_employee_skills(self, form_data, employee_id: int) -> None:
        certified_indices = form_data.getlist('skill_certified[]')
        self.db.execute(
            employee_skills.delete().where(employee_skills.c.employee_id == employee_id)
        )

        # Extract skill data
        skill_names = form_data.getlist('skill_name[]')
        skill_categories = form_data.getlist('skill_category[]')
        skill_levels = form_data.getlist('skill_level[]')

        for idx, (name, category, level) in enumerate(zip(skill_names, skill_categories, skill_levels)):
            name = name.strip()
            if not name:
                continue

            is_certified = str(idx) in certified_indices  # ✅ Check if this skill was marked certified

            # Find or create skill
            skill = self.db.query(Skill).filter_by(skill_name=name).first()
            if not skill:
                skill = Skill(
                    skill_name=name,
                    category_id=int(category) if category and category != "select category" else None
                )
                self.db.add(skill)
                self.db.flush()

            # Insert into association table with metadata
            self.db.execute(employee_skills.insert().values(
                employee_id=employee_id,
                skill_id=skill.skill_id,
                skill_level=level if level and level != "select level" else None,
                certified=is_certified  # ✅ Save certification status
            ))
    def get_employee_skills_with_metadata(self, employee_id):
        if callable(self.db):
         session = self.db()  # It's a factory, create a session
        else:
            session = self.db  # It's already a session
        try:
            result = session.execute(
                text("""
                    SELECT s.skill_name, sc.category_name, es.skill_level, es.certified
                    FROM employee_skills es
                    JOIN skills s ON s.skill_id = es.skill_id
                    LEFT JOIN skill_categories sc ON s.category_id = sc.category_id
                    WHERE es.employee_id = :emp_id
                """),
                {"emp_id": employee_id}
            )

            return result.fetchall()
        finally:
            session.close()



