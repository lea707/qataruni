from datetime import datetime
from models import Employee
from database.connection import db
from sqlalchemy.orm import joinedload


class EmployeeRepository:
    def __init__(self):
        pass

    def create_employee(self, form_data) -> int:
        required_fields = ['emp_id', 'arab_name', 'english_name', 'email', 'hire_date', 'position_id', 'department_id']
        for field in required_fields:
            if not form_data.get(field):
                raise ValueError(f"Missing required field: {field}")

        try:
            hire_date = datetime.strptime(form_data.get('hire_date'), '%Y-%m-%d').date()
            position_id = int(form_data.get('position_id'))
            department_id = int(form_data.get('department_id'))
            level_id = int(form_data.get('level_id', 1))
            supervisor_emp_id = form_data.get('supervisor_emp_id')
            if supervisor_emp_id:
                supervisor_emp_id = int(supervisor_emp_id)
        except Exception as e:
            raise ValueError(f"Invalid input format: {e}")

        employee_data = {
    'emp_id': form_data.get('emp_id'),
    'busness_id': self._generate_business_id(),
    'arab_name': form_data.get('arab_name'),
    'english_name': form_data.get('english_name'),
    'email': form_data.get('email'),
    'phone': form_data.get('phone'),
    'hire_date': hire_date,
    'position_id': position_id,
    'department_id': department_id,
    'level_id': level_id,
    'supervisor_emp_id': supervisor_emp_id,
    'skills': self._process_skills_form_data(form_data)
}

        return self._save_to_database(employee_data)

    def get_all_employees(self):
        return db.query(Employee).options(
            joinedload(Employee.department),
            joinedload(Employee.position)
        ).all()

    def _generate_business_id(self):
        last_employee = db.query(Employee).order_by(Employee.emp_id.desc()).first()
        next_id = last_employee.emp_id + 1 if last_employee else 1
        return f"BIZ{datetime.now().year}-{str(next_id).zfill(4)}"
    def _process_skills_form_data(self, form_data):
        return form_data.get('skills', [])
    
    def _save_to_database(self, employee_data):
     employee = Employee(**employee_data)
     db.add(employee)
     db.commit()
     return employee.emp_id