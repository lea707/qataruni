from database.connection import SessionLocal
from models.department import Department
from typing import List, Optional

class DepartmentRepository:
    def get_all_departments(self) -> List[Department]:
        session = SessionLocal()
        try:
            return session.query(Department).order_by(Department.department_name).all()
        finally:
            session.close()

    def get_department(self, department_id: int) -> Optional[Department]:
        session = SessionLocal()
        try:
            return session.query(Department).filter_by(department_id=department_id).first()
        finally:
            session.close()

    def create_department(self, department_data: dict) -> int:
        session = SessionLocal()
        try:
            new_department = Department(
                department_name=department_data['name'],
                director_emp_id=department_data.get('director_emp_id'),
                parent_department_id=department_data.get('parent_department_id')
            )
            session.add(new_department)
            session.commit()
            return new_department.department_id
        finally:
            session.close()

    def update_department(self, department_id: int, update_data: dict) -> bool:
        session = SessionLocal()
        try:
            department = session.query(Department).filter_by(department_id=department_id).first()
            if not department:
                return False

            if 'name' in update_data:
                department.department_name = update_data['name']
            if 'director_emp_id' in update_data:
                department.director_emp_id = update_data['director_emp_id']
            if 'parent_department_id' in update_data:
                department.parent_department_id = update_data['parent_department_id']

            session.commit()
            return True
        finally:
            session.close()

    def delete_department(self, department_id: int) -> bool:
        session = SessionLocal()
        try:
            department = session.query(Department).filter_by(department_id=department_id).first()
            if not department:
                return False

            session.delete(department)
            session.commit()
            return True
        finally:
            session.close()