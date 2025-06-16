from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Sample employee data
employees = [
    {"id": 1, "name": "Lea Smith", "department": "IT", "skills": ["Python", "Flask"]},
    {"id": 2, "name": "John Doe", "department": "Marketing", "skills": ["SEO", "Content"]}
]

@app.route('/')
def home():
    """Home page with navigation to other sections"""
    return render_template('index.html')

@app.route('/employees', endpoint='employees')  # Explicit endpoint added
def list_employees():
    """Display employee directory"""
    return render_template('employees.html', employees=employees)

@app.route('/employees/add', methods=['GET', 'POST'])
def add_employee():
    """Add new employee (form)"""
    if request.method == 'POST':
        new_id = max(e['id'] for e in employees) + 1
        new_employee = {
            "id": new_id,
            "name": request.form['name'],
            "department": request.form['department'],
            "skills": request.form.getlist('skills')
        }
        employees.append(new_employee)
        return redirect(url_for('employees'))  # Using endpoint name
    return render_template('add_employee.html')

@app.route('/employees/<int:employee_id>')
def employee_detail(employee_id):
    """Show single employee details"""
    employee = next((e for e in employees if e['id'] == employee_id), None)
    if not employee:
        return render_template('404.html'), 404
    return render_template('employee_detail.html', employee=employee)

@app.route('/about')
def about():
    """About page with contact info"""
    return render_template('about.html')

@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    return response

if __name__ == '__main__':
    app.run(debug=True)