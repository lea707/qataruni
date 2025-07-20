

from flask import session, flash, redirect, url_for, render_template
from .authentication import authenticate_user, get_user_permissions

def process_login(request):
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        print(f"Login attempt: username={username}")
        user = authenticate_user(username, password)
        if user:
            print(f"User authenticated: {user.username} (id={user.user_id})")
            session['user_id'] = user.user_id
            session['username'] = user.username
            session['permissions'] = list(user.permissions) if hasattr(user, 'permissions') else []
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            print("Authentication failed.")
            flash('Invalid username or password.', 'danger')
    return render_template('users/login.html')
