from flask import Flask, render_template, request
from routes import init_routes  # Import route initialization function

def create_app():
    app = Flask(__name__)
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        return response
    @app.errorhandler(404)
    def not_found(error):
     return render_template('404.html', path=request.path), 404
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('500.html'), 500
    init_routes(app)
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
