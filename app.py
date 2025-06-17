# app.py
from flask import Flask
from routes import init_routes

def create_app():
    app = Flask(__name__)
    
    # Security headers
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