from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from users.services.authentication import authenticate_user
from users.services.login import process_login
from sqlalchemy.orm import joinedload
from users.models.models import Role, Permission
from database.connection import SessionLocal
from werkzeug.exceptions import abort

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

@user_bp.route('/account/delete', methods=['POST'])
def delete_account():
    from users.models.models import User
    from database.connection import SessionLocal
    user_id = session.get('user_id')
    if not user_id:
        flash('You must be logged in to delete your account.', 'danger')
        return redirect(url_for('user.login'))
    db_session = SessionLocal()
    user = db_session.query(User).filter_by(user_id=user_id).first()
    if not user:
        db_session.close()
        flash('User not found.', 'danger')
        return redirect(url_for('user.login'))
    db_session.delete(user)
    db_session.commit()
    db_session.close()
    session.clear()
    flash('Your account has been deleted.', 'success')
    return redirect(url_for('user.login'))

@user_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    from users.services.account_service import register_user
    if request.method == 'POST':
        form_data = request.form.to_dict()
        success, message = register_user(form_data)
        if success:
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('user.login'))
        else:
            flash(message or 'Failed to create account.', 'danger')
            return render_template('signup.html', form_data=form_data, show_navbar=False)
    return render_template('signup.html', show_navbar=False)

@user_bp.route('/logout', methods=['POST'])
def logout():
    from flask import session, redirect, url_for, flash
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('user.login'))

# --- Role Management (Admin only) ---
@user_bp.route('/admin/roles')
def list_roles():
    if session.get('role_name') != 'Admin':
        abort(403)
    db_session = SessionLocal()
    roles = db_session.query(Role).options(joinedload(Role.permissions)).all()
    db_session.close()
    return render_template('admin/roles/list.html', roles=roles)

@user_bp.route('/admin/roles/<int:role_id>')
def view_role(role_id):
    if session.get('role_name') != 'Admin':
        abort(403)
    db_session = SessionLocal()
    role = db_session.query(Role).options(joinedload(Role.permissions)).filter_by(role_id=role_id).first()
    permissions = db_session.query(Permission).all()
    db_session.close()
    if not role:
        flash('Role not found.', 'danger')
        return redirect(url_for('user.list_roles'))
    return render_template('admin/roles/view.html', role=role, permissions=permissions)

@user_bp.route('/admin/roles/create', methods=['GET', 'POST'])
def create_role():
    if session.get('role_name') != 'Admin':
        abort(403)
    db_session = SessionLocal()
    permissions = db_session.query(Permission).all()
    if request.method == 'POST':
        name = request.form.get('role_name')
        perm_ids = request.form.getlist('permissions')
        if not name:
            flash('Role name is required.', 'danger')
            return render_template('admin/roles/create.html', permissions=permissions)
        role = Role(role_name=name)
        db_session.add(role)
        db_session.commit()
        # Assign permissions
        for pid in perm_ids:
            perm = db_session.query(Permission).filter_by(permission_id=pid).first()
            if perm:
                role.permissions.append(perm)
        db_session.commit()
        flash('Role created successfully.', 'success')
        db_session.close()
        return redirect(url_for('user.list_roles'))
    db_session.close()
    return render_template('admin/roles/create.html', permissions=permissions)

@user_bp.route('/admin/roles/<int:role_id>/edit', methods=['GET', 'POST'])
def edit_role(role_id):
    if session.get('role_name') != 'Admin':
        abort(403)
    db_session = SessionLocal()
    role = db_session.query(Role).options(joinedload(Role.permissions)).filter_by(role_id=role_id).first()
    permissions = db_session.query(Permission).all()
    if not role:
        db_session.close()
        flash('Role not found.', 'danger')
        return redirect(url_for('user.list_roles'))
    if request.method == 'POST':
        name = request.form.get('role_name')
        perm_ids = request.form.getlist('permissions')
        if not name:
            flash('Role name is required.', 'danger')
            return render_template('admin/roles/edit.html', role=role, permissions=permissions)
        role.role_name = name
        # Update permissions
        role.permissions.clear()
        for pid in perm_ids:
            perm = db_session.query(Permission).filter_by(permission_id=pid).first()
            if perm:
                role.permissions.append(perm)
        db_session.commit()
        flash('Role updated successfully.', 'success')
        db_session.close()
        return redirect(url_for('user.list_roles'))
    db_session.close()
    return render_template('admin/roles/edit.html', role=role, permissions=permissions)

@user_bp.route('/admin/roles/<int:role_id>/delete', methods=['POST'])
def delete_role(role_id):
    if session.get('role_name') != 'Admin':
        abort(403)
    db_session = SessionLocal()
    role = db_session.query(Role).filter_by(role_id=role_id).first()
    if not role:
        db_session.close()
        flash('Role not found.', 'danger')
        return redirect(url_for('user.list_roles'))
    db_session.delete(role)
    db_session.commit()
    db_session.close()
    flash('Role deleted.', 'success')
    return redirect(url_for('user.list_roles')) 