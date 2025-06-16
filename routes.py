from flask import Flask, render_template, request, redirect, url_for

employees = [
    {
        "id": 1,
        "name": "Lea Smith",
        "department": "IT",
        "skills": {
            "Technical": ["Python (Flask)", "SQL", "Docker"],
            "Business": ["Project Management"],
            "Languages": {"English": "Fluent", "Arabic": "Native"}
        }
    },
    {
        "id": 2,
        "name": "John Doe",
        "department": "Marketing",
        "skills": {
            "Technical": ["SEO", "Google Analytics", "Social Media Management"],
            "Business": ["Content Strategy", "Brand Management"],
            "Languages": {"English": "Native", "Arabic": "Intermediate"}
        }
    }
]

def init_routes(app):
    @app.route('/')
    def home():
        """Home page with navigation to other sections"""
        return render_template('index.html')

    @app.route('/employees', endpoint='employees')
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
                "skills": {
                    "Technical": request.form.getlist('technical_skills'),
                    "Business": request.form.getlist('business_skills'),
                    "Languages": {"English": request.form.get('english_level')}
                }
            }
            employees.append(new_employee)
            return redirect(url_for('list_employees'))
        return render_template('add_employee.html')

    @app.route('/employees/<int:employee_id>')
    def employee_detail(employee_id):
     try:
        employee = next((e for e in employees if e['id'] == employee_id), None)
        if not employee:
            return render_template(
                '404.html',
                employee_id=employee_id,
                path=request.path
            ), 404
        return render_template('employee_detail.html', employee=employee)
     except Exception as e:
        app.logger.error(f"Error fetching employee {employee_id}: {str(e)}")
        return render_template('500.html'), 500
    @app.route('/about')
    def about():
        """About page with contact info"""
        return render_template('about.html')

    @app.route('/search', methods=['GET'])
    def search_employees():
        """Search employees based on various criteria"""
        search_id = request.args.get('id')
        search_name = request.args.get('name', '').lower()
        search_department = request.args.get('department')
        search_skill = request.args.get('skill', '').lower()

        filtered_employees = employees

        if search_id:
            filtered_employees = [e for e in filtered_employees if e['id'] == int(search_id)]
        
        if search_name:
            filtered_employees = [e for e in filtered_employees if search_name in e['name'].lower()]
        
        if search_department:
            filtered_employees = [e for e in filtered_employees if e['department'] == search_department]
        
        if search_skill:
            filtered_employees = [
                e for e in filtered_employees 
                if any(search_skill in skill.lower() for skill in e['skills']['Technical'])
            ]

        return render_template('search.html', employees=filtered_employees)

    @app.route('/department/<dept_name>')
    def department(dept_name):
        dept_employees = [e for e in employees if e['department'].lower() == dept_name.lower()]
        return render_template('department.html', 
                            employees=dept_employees,
                            department=dept_name)
    

    @app.errorhandler(404)
    def page_not_found(error):
        """Handle 404 errors for both employee and non-employee pages"""
        # Get employee_id from either view_args or by parsing the path
        employee_id = None
        if request.view_args:
            employee_id = request.view_args.get('employee_id')
        elif request.path.startswith('/employees/'):
            try:
                employee_id = int(request.path.split('/')[-1])
            except (ValueError, IndexError):
                pass
        
        return render_template(
            '404.html',
            path=request.path,
            employee_id=employee_id
        ), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors"""
        app.logger.error(f"Server Error: {error}")
        return render_template('500.html'), 500

    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        return response