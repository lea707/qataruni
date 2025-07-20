from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from users.services.authentication import authenticate_user
from users.services.login import process_login
from sqlalchemy.orm import joinedload

user_bp = Blueprint('user', __name__, url_prefix='/user', template_folder='templates/users')

def has_permission(permission):
    from flask import session
    return session.get('permissions') and permission in session['permissions']

@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    return process_login(request)

@user_bp.route('/account', methods=['GET'])
def account():
    from users.models.models import User
    from database.connection import SessionLocal
    from flask import session, render_template, redirect, url_for, flash
    user_id = session.get('user_id')
    if not user_id:
        flash('You must be logged in to view your account.', 'danger')
        return redirect(url_for('user.login'))
    db_session = SessionLocal()
    user = db_session.query(User).options(joinedload(User.role)).filter_by(user_id=user_id).first()
    db_session.close()
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('user.login'))
    return render_template('users/account.html', user=user)

@user_bp.route('/account/update', methods=['POST'])
def update_account():
    from flask import session, request, redirect, url_for, flash, render_template
    from users.services.account_service import update_user_account
    from users.models.models import User
    from database.connection import SessionLocal
    user_id = session.get('user_id')
    if not user_id:
        flash('You must be logged in to update your account.', 'danger')
        return redirect(url_for('user.login'))
    form_data = request.form.to_dict()
    success, message = update_user_account(user_id, form_data)
    if success:
        flash('Account updated successfully.', 'success')
        return redirect(url_for('user.account'))
    else:
        flash(message or 'Failed to update account.', 'danger')
        # Re-fetch user for display
        db_session = SessionLocal()
        user = db_session.query(User).filter_by(user_id=user_id).first()
        db_session.close()
        return render_template('users/account.html', user=user)

@user_bp.route('/logout', methods=['POST'])
def logout():
    from flask import session, redirect, url_for, flash
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('user.login')) 