
from flask import render_template, request, redirect, url_for, flash
from services.employee_service import EmployeeService
from models.employee import EmployeeCollection
employee_service = EmployeeService()

def init_routes(app):
    @app.route('/')
    def home():
        return render_template('index.html')

    @app.route('/employees')
    def list_employees():
        employees = employee_service.employees
        return render_template('employees/list.html', employees=employees)

    @app.route('/employees/add', methods=['GET', 'POST'])
    def add_employee():
        if request.method == 'POST':
            employee_service.add_employee(request.form)
            flash("Employee added successfully!", "success")
            return redirect(url_for('list_employees'))
        return render_template('employees/add.html', departments=employee_service.departments)

    @app.route('/employees/<int:employee_id>')
    def employee_detail(employee_id):
        employee = employee_service.get(employee_id)
        if not employee:
            return render_template('404.html', employee_id=employee_id), 404
        return render_template('employees/details.html', employee=employee)

    @app.route('/departments/add', methods=['GET', 'POST'])
    def add_department():
        if request.method == 'POST':
            name = request.form.get('name')
            if employee_service.add_department(name):
                flash(f"Department '{name}' added!", "success")
            else:
                flash(f"Department '{name}' already exists!", "warning")
            return redirect(url_for('list_departments'))
        return render_template('departments/add.html')

    @app.route('/departments')
    def list_departments():
        return render_template('departments/departments_list.html',
                            departments=employee_service.departments)

    @app.route('/about')
    def about():
        return render_template('about.html')

    @app.route('/search')
    def search():
        filters = {k: v for k, v in request.args.items() if v}
        return render_template('search.html',
                            employees=employee_service.search(filters),  
                            departments=employee_service.departments)

    @app.route('/department')
    @app.route('/department/<dept_name>')
    def department(dept_name=None):
        if dept_name:
            employees = employee_service.search_employees({'department': dept_name})
            return render_template('departments/department.html', employees=employees, department=dept_name)
        departments = employee_service.departments
        all_employees = employee_service.employees
        return render_template('departments/departments_list.html', departments=departments, all_employees=all_employees)

    @app.errorhandler(404)
    def page_not_found(error):
        employee_id = None
        if request.view_args:
            employee_id = request.view_args.get('employee_id')
        elif request.path.startswith('/employees/'):
            try:
                employee_id = int(request.path.split('/')[-1])
            except (ValueError, IndexError):
                pass
        return render_template('404.html', path=request.path, employee_id=employee_id), 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Server Error: {error}")
        return render_template('500.html'), 500