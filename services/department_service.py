# services/department_service.py
from database.repositories.department_repository import DepartmentRepository
from models.department import Department
from typing import List, Optional
class DepartmentService:
    def __init__(self):
        self.repository = DepartmentRepository()

    def get_all_departments(self) -> List[Department]:
        return self.repository.get_all_departments()

    def get_department(self, department_id: int) -> Optional[Department]:
        """Get a single department by ID"""
        return self.repository.get_department(department_id)

    def create_department(self, name: str, director_emp_id: int = None, parent_id: int = None) -> int:
        """Create a new department"""
        if not name:
            raise ValueError("Department name is required")
            
        department_data = {
            'name': name,
            'director_emp_id': director_emp_id,
            'parent_department_id': parent_id
        }
        
        try:
            return self.repository.create_department(department_data)
        except ValueError as e:
            raise ValueError(f"Could not create department: {str(e)}")

    def update_department(self, department_id: int, **kwargs) -> bool:
        """Update department attributes"""
        valid_fields = {'name', 'director_emp_id', 'parent_department_id'}
        update_data = {k: v for k, v in kwargs.items() if k in valid_fields and v is not None}
        
        if not update_data:
            raise ValueError("No valid fields provided for update")
            
        return self.repository.update_department(department_id, update_data)

    def delete_department(self, department_id: int) -> bool:
        """Delete a department"""
        return self.repository.delete_department(department_id)