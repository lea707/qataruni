import os
from flask import Flask, g, request
from routes import init_routes
from urllib.parse import urlencode

def test_create_employee_success():
    print("Running test_create_employee_success")

def create_app():
    app = Flask(__name__)
    @app.before_request
    def load_fake_admin():
        g.current_user = {
            "username": "admin",
            "permissions": [
                "view_employee",
                "edit_employee",
                "delete_employee",
                "add_employee"
            ]
        }

    # ✅ Security headers
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        return response

    app.secret_key = '973ybbfehfehuhnencuen'
    init_routes(app)
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)