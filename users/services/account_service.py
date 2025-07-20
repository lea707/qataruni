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