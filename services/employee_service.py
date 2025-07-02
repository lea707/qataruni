from database.repositories.employee_repository import EmployeeRepository
from database.repositories.position_repository import PositionRepository
from database.repositories.skill_repository import SkillRepository


class EmployeeService:
    def __init__(self):
        self.repository = EmployeeRepository()
        self.position_repository = PositionRepository()
        self.skill_repository = SkillRepository()

    def create_employee(self, form_data) -> int:
        # Validate required fields
        required_fields = ['emp_id', 'arab_name', 'english_name', 'email', 'hire_date', 'position_id', 'department_id']
        for field in required_fields:
            if not form_data.get(field):
                raise ValueError(f"Missing required field: {field}")

        # Delegate to repository
        return self.repository.create_employee(form_data)

    def get_all_employees(self):
        return self.repository.get_all_employees()
    def get_all_positions(self):
        return self.position_repository.get_all_positions()
    def get_all_skills(self):
        return self.skill_repository.get_all_skills()
    def add_employee_with_documents(self, form_data, files):
        try:
            employee_id = self.create_employee(form_data)
            from services.employee_document_service import EmployeeDocumentService
            document_service = EmployeeDocumentService()
            document_service.handle_uploads(employee_id, form_data, files)
            return True
        except Exception as e:
            import logging
            logging.error(f"Error creating employee with documents: {e}")
            return False