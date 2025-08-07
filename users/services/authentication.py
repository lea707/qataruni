from users.models.models import User, Role
from werkzeug.security import check_password_hash
from flask import current_app
from sqlalchemy.orm import scoped_session, sessionmaker, joinedload
from database.connection import engine

def get_user_permissions(user):
    """
    Return a set of permission names for the given user (based on their role).
    """
    if not user or not user.role:
        return set()
    return set(p.permission_name for p in user.role.permissions)

def authenticate_user(username, password):
    Session = scoped_session(sessionmaker(bind=engine))
    db_session = Session()
    try:
        print(f"[DEBUG] Attempting login for username: {username}")
        user = db_session.query(User).options(
            joinedload(User.role).joinedload(Role.permissions)
        ).filter_by(username=username).first()
        if user:
            print(f"[DEBUG] User found. is_active: {user.is_active}")
            print(f"[DEBUG] Entered password: {password}")
            print(f"[DEBUG] Stored hash: {user.password_hash}")
            password_check = check_password_hash(user.password_hash, password)
            print(f"[DEBUG] Password check result: {password_check}")
            if user.is_active and password_check:
                # Check if linked employee is active (if emp_id is set)
                if user.emp_id:
                    from models.employee import Employee
                    employee = db_session.query(Employee).filter_by(emp_id=user.emp_id).first()
                    if not employee or not employee.is_active:
                        print("[DEBUG] Linked employee is not active.")
                        return None, 'Your account is deactivated. Please contact HR.'
                # Eagerly load permissions for session storage
                user.permissions = get_user_permissions(user)
                return user, None
        else:
            print("[DEBUG] No user found with that username.")
        return None, 'Invalid username or password.'
    finally:
        db_session.close() 