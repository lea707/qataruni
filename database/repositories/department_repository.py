from database.connection import db
from models.department import Department
from models.employee import Employee
from models.position import Position
from typing import List, Optional

class DepartmentRepository:

    def get_all_departments(self) -> List[Department]:
        return db.query(Department).order_by(Department.department_name).all()

    def get_department(self, department_id: int) -> Optional[Department]:
        return db.query(Department).filter_by(department_id=department_id).first()

    def create_department(self, department_data: dict) -> int:
        new_department = Department(
            department_name=department_data['name'],
            director_emp_id=department_data.get('director_emp_id'),
            parent_department_id=department_data.get('parent_department_id')
        )
        db.add(new_department)
        db.commit()
        return new_department.department_id

    def update_department(self, department_id: int, update_data: dict) -> bool:
        department = db.query(Department).filter_by(department_id=department_id).first()
        if not department:
            return False

        if 'name' in update_data:
            department.department_name = update_data['name']
        if 'director_emp_id' in update_data:
            department.director_emp_id = update_data['director_emp_id']
        if 'parent_department_id' in update_data:
            department.parent_department_id = update_data['parent_department_id']

        db.commit()
        return True

    def delete_department(self, department_id: int) -> bool:
        department = db.query(Department).filter_by(department_id=department_id).first()
        if not department:
            return False

        db.delete(department)
        db.commit()
        return True