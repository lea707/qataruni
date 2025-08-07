

from flask import session, flash, redirect, url_for, render_template
from .authentication import authenticate_user, get_user_permissions
from utils.role_helpers import get_director_department_ids

def process_login(request):
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        print(f"Login attempt: username={username}")
        user, error = authenticate_user(username, password)
        if user:
            print(f"User authenticated: {user.username} (id={user.user_id})")
            from database.connection import SessionLocal
            from models.employee import Employee
            from models.department import Department
            
            db_session = SessionLocal()
            try:
                session['user_id'] = user.user_id
                session['username'] = user.username
                session['permissions'] = list(user.permissions) if hasattr(user, 'permissions') else []
                session['role_name'] = user.role.role_name if user.role else None
                session['emp_id'] = user.emp_id if hasattr(user, 'emp_id') else None
                
                # Store department info if user is an employee
                if user.emp_id:
                    employee = db_session.query(Employee).filter_by(emp_id=user.emp_id).first()
                    if employee:
                        session['department_id'] = employee.department_id
                        # If user is a director, store their department IDs
                        if session['role_name'] == 'Director':
                            session['director_dept_ids'] = get_director_department_ids()
            finally:
                db_session.close()
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            print("Authentication failed.")
            flash(error or 'Invalid username or password.', 'danger')
    return render_template('login.html', show_navbar=False)
