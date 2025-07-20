from datetime import datetime
from sqlalchemy.orm import joinedload
from models import Employee, Skill, Position, Department, EmployeeLevel
from database.connection import SessionLocal
from typing import List, Optional

class EmployeeRepository:
    def _generate_business_id(self, session) -> str:
        try:
            employee_count = session.query(Employee).count()
            return f"BIZ{datetime.now().year}-{(employee_count + 1):04d}"
        except Exception as e:
            session.rollback()
            raise RuntimeError(f"Business ID generation failed: {e}")

    def create_employee(self, form_data: dict) -> int:
        session = SessionLocal()
        try:
            required_fields = ['arab_name', 'english_name', 'email', 'hire_date', 
                               'position_id', 'department_id', 'level_id']
            for field in required_fields:
                if not form_data.get(field):
                    raise ValueError(f"Missing required field: {field}")

            hire_date = form_data.get('hire_date')
            if isinstance(hire_date, str):
                hire_date = datetime.strptime(hire_date, '%Y-%m-%d').date()

            employee_data = {
                'busness_id': self._generate_business_id(session),
                'arab_name': form_data.get('arab_name'),
                'english_name': form_data.get('english_name'),
                'email': form_data.get('email'),
                'phone': form_data.get('phone'),
                'hire_date': hire_date,
                'position_id': int(form_data.get('position_id')),
                'department_id': int(form_data.get('department_id')),
                'level_id': int(form_data.get('level_id')),
                'supervisor_emp_id': int(form_data['supervisor_emp_id']) if form_data.get('supervisor_emp_id') else None,
                'is_active': form_data.get('is_active', 'false').lower() == 'true',
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }

            employee = Employee(**employee_data)
            session.add(employee)
            session.flush()

            if 'skill_ids[]' in form_data:
                self._process_employee_skills(session, employee.emp_id, form_data.getlist('skill_ids[]'))

            session.commit()
            return employee.emp_id
        except Exception as e:
            session.rollback()
            raise RuntimeError(f"Failed to save employee: {e}")
        finally:
            session.close()

    def _process_employee_skills(self, session, employee_id: int, skill_ids: List[str]) -> None:
        employee = session.query(Employee).get(employee_id)
        if not employee:
            raise ValueError("Employee not found")
        employee.skills = []
        for skill_id in skill_ids:
            if skill_id:
                skill = session.query(Skill).get(int(skill_id))
                if skill:
                    employee.skills.append(skill)

    def get_all_employees(self) -> List[Employee]:
        session = SessionLocal()
        try:
            return session.query(Employee).options(
                joinedload(Employee.department),
                joinedload(Employee.position),
                joinedload(Employee.level),
                joinedload(Employee.skills),
                joinedload(Employee.documents)
            ).order_by(Employee.emp_id).all()
        finally:
            session.close()

    def get_employee(self, employee_id: int) -> Optional[Employee]:
        session = SessionLocal()
        try:
            return session.query(Employee).options(
                joinedload(Employee.department),
                joinedload(Employee.position),
                joinedload(Employee.level),
                joinedload(Employee.skills),
                joinedload(Employee.documents),
                joinedload(Employee.supervisor)  # Eagerly load supervisor
            ).filter(Employee.emp_id == employee_id).first()
        finally:
            session.close()

    def update_employee(self, employee_id: int, form_data: dict) -> bool:
        session = SessionLocal()
        try:
            employee = session.query(Employee).get(employee_id)
            if not employee:
                return False

            employee.english_name = form_data.get('english_name', employee.english_name)
            employee.arab_name = form_data.get('arab_name', employee.arab_name)
            employee.email = form_data.get('email', employee.email)
            employee.phone = form_data.get('phone', employee.phone)

            if form_data.get('hire_date'):
                hire_date = form_data.get('hire_date')
                if isinstance(hire_date, str):
                    hire_date = datetime.strptime(hire_date, '%Y-%m-%d').date()
                employee.hire_date = hire_date

            employee.position_id = int(form_data.get('position_id', employee.position_id))
            employee.department_id = int(form_data.get('department_id', employee.department_id))
            employee.level_id = int(form_data.get('level_id', employee.level_id))
            employee.supervisor_emp_id = int(form_data['supervisor_emp_id']) if form_data.get('supervisor_emp_id') else None
            employee.is_active = form_data.get('is_active', str(employee.is_active)).lower() == 'true'
            employee.updated_at = datetime.utcnow()

            if 'skill_ids[]' in form_data:
                self._process_employee_skills(session, employee_id, form_data.getlist('skill_ids[]'))

            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error updating employee: {e}")
            return False
        finally:
            session.close()

    def delete_employee(self, employee_id: int) -> bool:
        session = SessionLocal()
        try:
            employee = session.query(Employee).filter_by(emp_id=employee_id).first()
            if not employee:
                return False
            session.delete(employee)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error deleting employee: {e}")
            return False
        finally:
            session.close()