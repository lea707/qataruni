from database.connection import SessionLocal
from models.department import Department
from typing import List, Optional
from sqlalchemy.orm import joinedload
from models.employee import Employee
from models.position import Position 
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
            return session.query(Department).options(
                joinedload(Department.employees).joinedload(Employee.level),
                joinedload(Department.employees).joinedload(Employee.position),
                joinedload(Department.director),
                joinedload(Department.parent_department)
            ).filter_by(department_id=department_id).first()
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
            
            # Prevent deletion if child departments exist
            child_departments = session.query(Department).filter_by(
                parent_department_id=department_id
            ).count()
            
            if child_departments > 0:
                return False
                
            # Prevent deletion if employees exist in this department
            employee_count = session.query(Employee).filter_by(department_id=department_id).count()
            if employee_count > 0:
                return False
            
            # Handle positions FIRST - reassign them to a different department
            positions = session.query(Position).filter_by(department_id=department_id).all()
            
            for position in positions:
                # Reassign position to unassigned department (ID 57) instead of deleting
                position.department_id = 57  # Unassigned department
            
            # Clear director reference
            if department.director_emp_id:
                department.director_emp_id = None
            
            # FLUSH all changes before deletion
            session.flush()
                
            # Now delete the department
            session.delete(department)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error deleting department: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            session.close()