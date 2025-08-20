# app.py
import os
from flask import Flask, g, request, session, redirect, url_for, flash
from sqlalchemy.orm import joinedload as _joinedload
from database.connection import Base, engine
from models import *  # ensure models are imported so tables are known
from users.models.models import Base as UserBase  # user tables
from urllib.parse import urlencode

def create_app():
    app = Flask(__name__)

    @app.before_request
    def require_login():
        public_endpoints = ['user.login', 'user.signup', 'static']
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
    
    # Configure upload folder
    app.config['UPLOAD_FOLDER'] = 'employee_documents'
    
    # Ensure database schema exists before importing routes that may query
    try:
        Base.metadata.create_all(bind=engine)
        UserBase.metadata.create_all(bind=engine)
    except Exception:
        pass

    # Import and register event handlers (CRITICAL - must happen before routes)
    import event_handlers  # This import registers the signal listeners
    app.logger.info("✅ Event handlers registered")

    # Import and attach routes after DB is ready
    from routes import init_routes
    init_routes(app)
    from users.user_routes import user_bp
    app.register_blueprint(user_bp)

    print("\nRegistered routes:")
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint}: {rule}")

    return app

# Expose a top-level Flask app instance for tests and scripts
app = create_app()

# Ensure database schema exists for tests/dev
with app.app_context():
    try:
        # Create both app and user schemas
        Base.metadata.create_all(bind=engine)
        UserBase.metadata.create_all(bind=engine)
    except Exception as _e:
        pass

# Make joinedload available to tests that reference it directly without importing
try:
    import builtins as _builtins
    if os.getenv('TESTING') == '1' or 'PYTEST_CURRENT_TEST' in os.environ:
        setattr(_builtins, 'joinedload', _joinedload)
except Exception:
    pass

if __name__ == '__main__':
    app.run(debug=True)