import os
from flask import Flask, g, request, session, redirect, url_for, flash
from routes import init_routes
from urllib.parse import urlencode

def test_create_employee_success():
    print("Running test_create_employee_success")

def create_app():
    app = Flask(__name__)

    @app.before_request
    def require_login():
        public_endpoints = ['user.login', 'static']
        if request.endpoint not in public_endpoints and not session.get('user_id'):
            flash('Please login or sign up to access this page.', 'danger')
            return redirect(url_for('user.login', next=request.url))


    # ✅ Security headers
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        return response

    app.secret_key = '973ybbfehfehuhnencuen'
    init_routes(app)
    from users.user_routes import user_bp
    app.register_blueprint(user_bp)
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)