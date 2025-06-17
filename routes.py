from flask import Flask, render_template, request, redirect, url_for

employees = [
    # Marketing Department
    {
        "id": 101,
        "name": "Fatima Al-Mansoori",
        "department": "Marketing",
        "skills": {
            "Technical": ["Digital Advertising", "Google Analytics", "SEO"],
            "Business": ["Brand Strategy", "Market Research"],
            "Languages": {"Arabic": "Native", "English": "Fluent"}
        }
    },
    
    # Admissions & Registration
    {
        "id": 102,
        "name": "Ahmed Al-Suwaidi",
        "department": "Admissions & Registration",
        "skills": {
            "Technical": ["Banner System", "Data Entry"],
            "Business": ["Student Counseling", "Policy Compliance"],
            "Languages": {"Arabic": "Native", "French": "Intermediate"}
        }
    },
    
    # Student Affairs
    {
        "id": 103,
        "name": "Mariam Al-Hashimi",
        "department": "Student Affairs",
        "skills": {
            "Technical": ["Event Management Software"],
            "Business": ["Conflict Resolution", "Student Mentoring"],
            "Languages": {"Arabic": "Native", "English": "Fluent", "Urdu": "Basic"}
        }
    },
    
    # Human Resources
    {
        "id": 104,
        "name": "Khalid Al-Nuaimi",
        "department": "Human Resources",
        "skills": {
            "Technical": ["HRIS Systems", "Payroll Software"],
            "Business": ["Recruitment", "Employee Relations"],
            "Languages": {"Arabic": "Native", "English": "Professional"}
        }
    },
    
    # Finance & Procurement
    {
        "id": 105,
        "name": "Noura Al-Khalifa",
        "department": "Finance & Procurement",
        "skills": {
            "Technical": ["SAP FI", "Excel Advanced"],
            "Business": ["Vendor Negotiation", "Budget Analysis"],
            "Languages": {"Arabic": "Native", "English": "Fluent"}
        }
    },
    
    # IT Services
    {
        "id": 106,
        "name": "Ali Al-Sulaiti",
        "department": "IT Services",
        "skills": {
            "Technical": ["Python", "Network Security", "Docker"],
            "Business": ["Project Management"],
            "Languages": {"Arabic": "Native", "English": "Fluent"}
        }
    },
    
    # Research & Graduate Studies
    {
        "id": 107,
        "name": "Dr. Yasmin Al-Mohannadi",
        "department": "Research & Graduate Studies",
        "skills": {
            "Technical": ["SPSS", "LaTeX"],
            "Business": ["Grant Writing", "Academic Publishing"],
            "Languages": {"Arabic": "Native", "English": "Fluent", "German": "Intermediate"}
        }
    },
    
    # Facilities & Maintenance
    {
        "id": 108,
        "name": "Ibrahim Al-Hamar",
        "department": "Facilities & Maintenance",
        "skills": {
            "Technical": ["HVAC Systems", "Electrical Maintenance"],
            "Business": ["Vendor Management"],
            "Languages": {"Arabic": "Native", "Hindi": "Conversational"}
        }
    },
    
    # International Affairs
    {
        "id": 109,
        "name": "Layla Al-Ansari",
        "department": "International Affairs",
        "skills": {
            "Technical": ["Immigration Software"],
            "Business": ["Cross-Cultural Communication", "Partnership Development"],
            "Languages": {"Arabic": "Native", "English": "Fluent", "Spanish": "Intermediate"}
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
        # Extract all unique departments from your employees data
        departments = sorted({e['department'] for e in employees})
        
        search_id = request.args.get('id')
        search_name = request.args.get('name', '').lower()
        search_department = request.args.get('department')
        technical_skill = request.args.get('technical_skill', '').lower()
        business_skill = request.args.get('business_skill', '').lower()
        languages_skill = request.args.get('languages_skill', '').lower()

        filtered_employees = employees

        if search_id:
            filtered_employees = [e for e in filtered_employees if e['id'] == int(search_id)]
        
        if search_name:
            filtered_employees = [e for e in filtered_employees if search_name in e['name'].lower()]
        
        if search_department:
            filtered_employees = [e for e in filtered_employees if e['department'] == search_department]
        
        if technical_skill:
            filtered_employees = [
                e for e in filtered_employees 
                if any(technical_skill in s.lower() 
                      for s in e['skills']['Technical'])
            ]
        
        if business_skill:
            filtered_employees = [
                e for e in filtered_employees 
                if any(business_skill in s.lower() 
                      for s in e['skills']['Business'])
            ]
            
        if languages_skill:
            filtered_employees = [
                e for e in filtered_employees 
                if any(languages_skill in lang.lower() 
                      for lang in e['skills']['Languages'].keys())
            ]

        return render_template(
            'search.html', 
            employees=filtered_employees,
            departments=departments
        )

    @app.route('/department')  # Handles "/department" URL
    @app.route('/department/<dept_name>')  # Keeps your existing filtered view
    def department(dept_name=None):
        if dept_name:
            # Existing single-department logic
            dept_employees = [e for e in employees 
                             if e['department'].lower() == dept_name.lower()]
            return render_template('department.html', 
                                employees=dept_employees,
                                department=dept_name)
        else:
            # New: List all departments
            departments = sorted({e['department'] for e in employees})  # Unique sorted list
            return render_template('departments_list.html', 
                                departments=departments,
                                all_employees=employees)  # Pass full list for counting

    @app.errorhandler(404)
    def page_not_found(error):
        """Handle 404 errors for both employee and non-employee pages"""
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