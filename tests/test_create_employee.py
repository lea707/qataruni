import unittest
from services.employee_service import EmployeeService

class TestCreateEmployee(unittest.TestCase):
    def setUp(self):
        self.service = EmployeeService()

    def test_create_employee_success(self):
        form_data = {
            'emp_id': 'E123',
            'arab_name': 'ليلى',
            'english_name': 'Lea',
            'email': 'lea@example.com',
            'hire_date': '2024-01-01',
            'position_id': 1,
            'department_id': 2,
            'level_id': 1,
            'supervisor_emp_id': None,
            'skills': []
        }
        result = self.service.create_employee(form_data)
        self.assertIsInstance(result, int)

    def test_missing_required_field(self):
        form_data = {
            'emp_id': 'E124',
            'arab_name': 'ليلى',
            'english_name': 'Lea',
            'email': 'lea@example.com',
            'hire_date': '2024-01-01',
            # 'position_id' is missing
            'department_id': 2
        }
        with self.assertRaises(ValueError) as context:
            self.service.create_employee(form_data)
        self.assertIn("Missing required field", str(context.exception))

    def test_invalid_date_format(self):
        form_data = {
            'emp_id': 'E125',
            'arab_name': 'ليلى',
            'english_name': 'Lea',
            'email': 'lea@example.com',
            'hire_date': '01-01-2024',  # Wrong format
            'position_id': 1,
            'department_id': 2
        }
        with self.assertRaises(ValueError) as context:
            self.service.create_employee(form_data)
        self.assertIn("Invalid input format", str(context.exception))

    def test_non_integer_position_id(self):
        form_data = {
            'emp_id': 'E126',
            'arab_name': 'ليلى',
            'english_name': 'Lea',
            'email': 'lea@example.com',
            'hire_date': '2024-01-01',
            'position_id': 'one',  # Invalid
            'department_id': 2
        }
        with self.assertRaises(ValueError) as context:
            self.service.create_employee(form_data)
        self.assertIn("Invalid input format", str(context.exception))

    def test_optional_fields_omitted(self):
        form_data = {
            'emp_id': 'E127',
            'arab_name': 'ليلى',
            'english_name': 'Lea',
            'email': 'lea@example.com',
            'hire_date': '2024-01-01',
            'position_id': 1,
            'department_id': 2
            # No phone, level_id, or supervisor_emp_id
        }
        result = self.service.create_employee(form_data)
        self.assertIsInstance(result, int)

if __name__ == '__main__':
    unittest.main()