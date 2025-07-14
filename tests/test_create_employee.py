from app import app
import unittest
import io
from datetime import date
from services.employee_service import EmployeeService
from models import Department, Position, EmployeeLevel, CertificateType, DocumentType
from models.employee import Employee
from models.employee_document import EmployeeDocument
from database.connection import db


class TestCreateEmployee(unittest.TestCase):
    def setUp(self):
        with app.app_context():
            self.service = EmployeeService()
            self.session = db()
            # Clean and seed required data
            self.session.query(EmployeeDocument).delete()
            self.session.query(Employee).delete()
            self.session.query(Department).delete()
            self.session.query(Position).delete()
            self.session.query(EmployeeLevel).delete()
            self.session.query(CertificateType).delete()
            self.session.query(DocumentType).delete()
            self.session.commit()
            self.department = Department(department_name="Engineering")
            self.position = Position(position_name="Developer")
            self.level = EmployeeLevel(level_name="Junior")
            self.cert_type = CertificateType(type_name="Language Certificate")
            self.doc_type = DocumentType(type_name="ID Document")
            self.session.add_all([self.department, self.position, self.level, self.cert_type, self.doc_type])
            self.session.commit()

    def tearDown(self):
        with app.app_context():
            self.session.query(EmployeeDocument).delete()
            self.session.query(Employee).delete()
            self.session.commit()
            self.session.close()

    def test_create_employee_success(self):
        with app.app_context():
            form_data = {
                'arab_name': 'ليلى',
                'english_name': 'Lea',
                'email': 'lea@example.com',
                'hire_date': '2024-01-01',
                'position_id': self.position.position_id,
                'department_id': self.department.department_id,
                'level_id': self.level.level_id,
                'supervisor_emp_id': '',
                'skills': []
            }
            result = self.service.create_employee(form_data)
            self.assertIsInstance(result, int)

    def test_missing_required_field(self):
        with app.app_context():
            form_data = {
                'arab_name': 'ليلى',
                'english_name': 'Lea',
                'email': 'lea@example.com',
                'hire_date': '2024-01-01',
                # Missing position_id
                'department_id': self.department.department_id
            }
            with self.assertRaises(ValueError) as context:
                self.service.create_employee(form_data)
            self.assertIn("Missing required field", str(context.exception))

    def test_invalid_date_format(self):
        with app.app_context():
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
        with app.app_context():
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
        with app.app_context():
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

    def test_create_employee_with_certificate_and_document(self):
        with app.app_context():
            form_data = {
                'arab_name': 'ليلى',
                'english_name': 'Lea',
                'email': 'lea@example.com',
                'phone': '12345678',
                'hire_date': date.today().isoformat(),
                'position_id': self.position.position_id,
                'department_id': self.department.department_id,
                'level_id': self.level.level_id,
                'supervisor_emp_id': '',
                'skill_name[]': 'Python',
                'skill_category[]': '1',
                'skill_level[]': 'Advanced',
                'certified[]': 'on',
                'certificate_type_id[]': str(self.cert_type.cert_type_id),
                'issuing_organization[]': 'Test Institute',
                'validity_period_months[]': '12',
                'general_document_type_id[]': str(self.doc_type.type_id)
            }
            files = {
                'document_file_0[]': (io.BytesIO(b"fake cert content"), 'cert.png'),
                'general_document_file[]': (io.BytesIO(b"fake doc content"), 'doc.png')
            }
            result = self.service.create_employee(form_data, files)
            self.assertIsInstance(result, int)
            employee = self.session.query(Employee).filter_by(emp_id=result).first()
            self.assertEqual(len(employee.documents), 2)

if __name__ == '__main__':
    unittest.main()