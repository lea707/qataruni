from users.models.models import User
from database.connection import SessionLocal
import re

def update_user_account(user_id, form_data):
    """
    Validate and update user account info. Returns (success, message).
    """
    db_session = SessionLocal()
    try:
        user = db_session.query(User).filter_by(user_id=user_id).first()
        if not user:
            print('[DEBUG] User not found for update.')
            return False, 'User not found.'
        # Validate username (required, 2-50 chars, letters/numbers/spaces/basic punctuation)
        username = form_data.get('username', '').strip()
        if not username:
            print('[DEBUG] Name is required.')
            return False, 'Name is required.'
        if not (2 <= len(username) <= 50):
            print('[DEBUG] Name length invalid.')
            return False, 'Name must be between 2 and 50 characters.'
        if not re.match(r"^[A-Za-z0-9 .,'-]+$", username):
            print('[DEBUG] Name contains invalid characters.')
            return False, 'Name contains invalid characters.'
        # Validate email (optional, valid format, unique)
        email = form_data.get('email', '').strip()
        if email:
            if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
                print('[DEBUG] Invalid email format.')
                return False, 'Invalid email format.'
            existing_email = db_session.query(User).filter(User.email == email, User.user_id != user_id).first()
            if existing_email:
                print('[DEBUG] Email already in use.')
                return False, 'Email is already in use.'
        # Validate phone number (optional, exactly 8 digits, unique)
        phone = form_data.get('phone_number', '').strip()
        if phone:
            if not re.match(r"^\d{8}$", phone):
                print('[DEBUG] Phone number must be exactly 8 digits.')
                return False, 'Phone number must be exactly 8 digits.'
            existing_phone = db_session.query(User).filter(User.phone_number == phone, User.user_id != user_id).first()
            if existing_phone:
                print('[DEBUG] Phone number already in use.')
                return False, 'Phone number is already in use.'
        # Validate business_user_id (optional, must match add employee regex, unique)
        business_id = form_data.get('business_user_id', '').strip()
        if business_id:
            if not re.match(r"^(?=.*[A-Za-z])(?=.*\d)(?=.*-)[A-Za-z\d-]{5,}$", business_id):
                print('[DEBUG] Business ID invalid.')
                return False, 'Business ID must be at least 5 characters, contain letters, numbers, and a dash (-).'
            existing_biz = db_session.query(User).filter(User.business_user_id == business_id, User.user_id != user_id).first()
            if existing_biz:
                print('[DEBUG] Business ID already in use.')
                return False, 'Business ID is already in use.'
        # User cannot change their role
        # Update fields
        print(f'[DEBUG] Updating user {user_id}:')
        print(f'  username: {user.username} -> {username}')
        print(f'  email: {user.email} -> {email}')
        print(f'  phone_number: {user.phone_number} -> {phone}')
        print(f'  business_user_id: {user.business_user_id} -> {business_id}')
        user.username = username
        user.email = email or None
        user.phone_number = phone or None
        user.business_user_id = business_id or None
        db_session.commit()
        print('[DEBUG] Commit successful.')
        return True, None
    except Exception as e:
        db_session.rollback()
        print(f'[DEBUG] Exception during update: {e}')
        return False, str(e)
    finally:
        db_session.close()

def register_user(form_data):
    """
    Validate and register a new user. Returns (success, message).
    """
    from users.models.models import User, Role
    from werkzeug.security import generate_password_hash
    from models.employee import Employee
    from database.connection import SessionLocal
    db_session = SessionLocal()
    try:
        # Required fields
        username = form_data.get('username', '').strip()
        password = form_data.get('password', '')
        password_confirm = form_data.get('password_confirm', '')
        email = form_data.get('email', '').strip()
        phone = form_data.get('phone_number', '').strip()
        business_id = form_data.get('business_user_id', '').strip()

        # Employee verification
        employee = db_session.query(Employee).filter_by(busness_id=business_id).first()
        if not employee:
            return False, 'You must be a registered employee to sign up.'
        if (employee.email or '').strip().lower() != email.lower() or (employee.phone or '').strip() != phone:
            return False, 'Business ID, email, and phone number do not match our records.'
        if not employee.is_active:
            return False, 'You are not an active employee and cannot create an account.'

        # Username validation
        if not username:
            return False, 'Username is required.'
        if not (2 <= len(username) <= 50):
            return False, 'Username must be between 2 and 50 characters.'
        if not re.match(r"^[A-Za-z0-9 .,'-]+$", username):
            return False, 'Username contains invalid characters.'
        if db_session.query(User).filter_by(username=username).first():
            return False, 'Username is already taken.'

        # Password validation
        if not password:
            return False, 'Password is required.'
        if len(password) < 6:
            return False, 'Password must be at least 6 characters.'
        if password != password_confirm:
            return False, 'Passwords do not match.'

        # Email validation
        if not email:
            return False, 'Email is required.'
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            return False, 'Invalid email format.'
        if db_session.query(User).filter_by(email=email).first():
            return False, 'Email is already in use.'

        # Phone validation
        if not phone:
            return False, 'Phone number is required.'
        if not re.match(r"^\d{8}$", phone):
            return False, 'Phone number must be exactly 8 digits.'
        if db_session.query(User).filter_by(phone_number=phone).first():
            return False, 'Phone number is already in use.'

        # Business ID validation
        if not business_id:
            return False, 'Business ID is required.'
        if not re.match(r"^(?=.*[A-Za-z])(?=.*\d)(?=.*-)[A-Za-z\d-]{5,}$", business_id):
            return False, 'Business ID must be at least 5 characters, contain letters, numbers, and a dash (-).'
        if db_session.query(User).filter_by(business_user_id=business_id).first():
            return False, 'Business ID is already in use.'

        # Assign role based on position and supervisor status
        # Get position name
        position_name = employee.position.position_name if employee.position else ''
        # Check if supervisor (has direct reports)
        is_supervisor = db_session.query(Employee).filter_by(supervisor_emp_id=employee.emp_id).first() is not None
        role_name = 'Employee'
        if position_name.lower() == 'director':
            role_name = 'Director'
        elif position_name.lower() == 'hr':
            role_name = 'HR'
        elif is_supervisor:
            role_name = 'Supervisor'
        # Get the role object
        assigned_role = db_session.query(Role).filter_by(role_name=role_name).first()
        if not assigned_role:
            return False, f'Role {role_name} not found. Contact admin.'

        # Create user
        user = User(
            username=username,
            password_hash=generate_password_hash(password),
            email=email,
            phone_number=phone,
            business_user_id=business_id,
            is_active=True,
            role=assigned_role,
            emp_id=employee.emp_id
        )
        db_session.add(user)
        db_session.commit()
        return True, None
    except Exception as e:
        db_session.rollback()
        return False, str(e)
    finally:
        db_session.close() 