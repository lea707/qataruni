from flask import session
from models.department import Department
from database.connection import db

def get_director_department_ids():
    """Get the director's department and all sub-departments."""
    user_role = session.get('role_name')
    user_emp_id = session.get('emp_id')
    if user_role != 'Director' or not user_emp_id:
        return []
    # Find the department where this user is the director
    director_dept = db().query(Department).filter_by(director_emp_id=user_emp_id).first()
    if not director_dept:
        return []
    # Recursively get all sub-department ids
    def get_sub_dept_ids(dept):
        ids = [dept.department_id]
        for sub in db().query(Department).filter_by(parent_department_id=dept.department_id).all():
            ids.extend(get_sub_dept_ids(sub))
        return ids
    return get_sub_dept_ids(director_dept) 