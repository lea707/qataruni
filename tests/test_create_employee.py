import unittest
from services.employee_service import EmployeeService
from models import Department, Position, EmployeeLevel
from database.connection import db
from models.employee import Employee

class TestCreateEmployee(unittest.TestCase):
    def setUp(self):
        self.service = EmployeeService()

        # Clean and seed required data
        db.query(Employee).delete()
        db.query(Department).delete()
        db.query(Position).delete()
        db.query(EmployeeLevel).delete()
        db.commit()
        self.department = Department(department_name="Engineering")
        self.position = Position(position_name="Developer")
        self.level = EmployeeLevel(level_name="Junior")

        db.add_all([self.department, self.position, self.level])
        db.commit()

    def test_create_employee_success(self):
        form_data = {
            'arab_name': 'ليلى',
            'english_name': 'Lea',
            'email': 'lea@example.com',
            'hire_date': '2024-01-01',
            'position_id': self.position.position_id,
            'department_id': self.department.department_id,
            'level_id': self.level.level_id,
            'supervisor_emp_id': None,
            'skills': []
        }
        result = self.service.create_employee(form_data)
        self.assertIsInstance(result, int)

    def test_missing_required_field(self):
        form_data = {
            'arab_name': 'ليلى',
            'english_name': 'Lea',
            'email': 'lea@example.com',
            'hire_date': '2024-01-01',
            # 'position_id' is missing
            'department_id': self.department.department_id
        }
        with self.assertRaises(ValueError) as context:
            self.service.create_employee(form_data)
        self.assertIn("Missing required field", str(context.exception))

    def test_invalid_date_format(self):
        form_data = {
            'arab_name': 'ليلى',
            'english_name': 'Lea',
            'email': 'lea@example.com',
            'hire_date': '01-01-2024',  # Wrong format
            'position_id': self.position.position_id,
            'department_id': self.department.department_id
        }
        with self.assertRaises(ValueError) as context:
            self.service.create_employee(form_data)
        self.assertIn("Invalid input format", str(context.exception))

    def test_non_integer_position_id(self):
        form_data = {
            'arab_name': 'ليلى',
            'english_name': 'Lea',
            'email': 'lea@example.com',
            'hire_date': '2024-01-01',
            'position_id': 'one',  # Invalid
            'department_id': self.department.department_id
        }
        with self.assertRaises(ValueError) as context:
            self.service.create_employee(form_data)
        self.assertIn("Invalid input format", str(context.exception))

    def test_optional_fields_omitted(self):
        form_data = {
            'arab_name': 'ليلى',
            'english_name': 'Lea',
            'email': 'lea@example.com',
            'hire_date': '2024-01-01',
            'position_id': self.position.position_id,
            'department_id': self.department.department_id
            # No phone, level_id, or supervisor_emp_id
        }
        result = self.service.create_employee(form_data)
        self.assertIsInstance(result, int)

if __name__ == '__main__':
    unittest.main()