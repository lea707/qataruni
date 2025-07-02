# routes.py
from flask import render_template, request, redirect, url_for, flash
from services.employee_service import EmployeeService
from services.department_service import DepartmentService
from flask import send_from_directory
from models.employee import Employee
from database.connection import db
from services.employee_document_service import EmployeeDocumentService
employee_service = EmployeeService()
department_service = DepartmentService()
employee_document_service = EmployeeDocumentService()
from services.level_service import LevelService
level_service = LevelService()
from models.position import Position
from models.department import Department
from models.level import EmployeeLevel
def init_routes(app):
    # Static files
    @app.route('/static/<path:filename>')
    def static_files(filename):
        response = send_from_directory(app.static_folder, filename)
        if filename.endswith('.css'):
            response.headers['Content-Type'] = 'text/css'
        return response

    # Main pages
    @app.route('/')
    def home():
        return render_template('index.html')

    @app.route('/about')
    def about():
        return render_template('about.html')

    # Employee routes
    @app.route('/employees')
    def list_employees():
        employees = employee_service.get_all_employees()
        return render_template('employees/list.html', employees=employees)
    @app.route('/employees/edit/<int:employee_id>', methods=['GET', 'POST'])
    @app.route('/employees/delete/<int:employee_id>', methods=['POST'])
    def delete_employee(employee_id):
     employee = db.get(Employee, employee_id)
     if not employee:
        return "Employee not found", 404

     db.delete(employee)
     db.commit()
     return redirect(url_for('list_employees'))
    def edit_employee(employee_id):
        employee = db.session.get(Employee, employee_id)
        if not employee:
            return "Employee not found", 404

        if request.method == 'POST':
            employee.busness_id = request.form['busness_id']
            employee.english_name = request.form['english_name']
            employee.arab_name = request.form['arab_name']
            db.session.commit()
            return redirect(url_for('list_employees'))
        return render_template('employees/edit.html', employee=employee)
    @app.route('/employees/add', methods=['GET', 'POST'])
    def add_employee():
        if request.method == 'POST':
            success = employee_service.add_employee_with_documents(request.form, request.files)
            if success:
                flash('Employee added successfully!', 'success')
                return redirect(url_for('list_employees'))
            else:
                flash('Failed to add employee.', 'error')

        # ✅ Load dynamic dropdown data
        positions = db.query(Position).order_by(Position.position_name).all()
        departments = db.query(Department).order_by(Department.department_name).all()
        levels = db.query(EmployeeLevel).order_by(EmployeeLevel.level_name).all()
        certificate_types = employee_document_service.get_all_certificate_types()
        document_types = employee_document_service.get_all_document_types()

        return render_template(
            'employees/add.html',
            positions=positions,
            departments=departments,
            levels=levels,
            certificate_types=certificate_types,
            document_types=document_types
        )



    @app.route('/employees/<int:employee_id>')
    def employee_detail(employee_id):
        employee = employee_service.get_employee(employee_id)
        if not employee:
            return render_template('404.html', employee_id=employee_id), 404
        return render_template('employees/details.html', employee=employee)

    # Department routes
    @app.route('/departments')
    def list_departments():
        departments = department_service.get_all_departments()
        return render_template('departments/list.html', departments=departments)

    @app.route('/departments/add', methods=['GET', 'POST'])
    def add_department():
        if request.method == 'POST':
            name = request.form.get('name')
            try:
                department_id = department_service.create_department(name)
                flash(f"Department '{name}' created successfully!", "success")
                return redirect(url_for('view_department', department_id=department_id))
            except ValueError as e:
                flash(str(e), "error")

        return render_template('departments/add.html')  # ✅ now always returns a response

    @app.route('/departments/<int:department_id>')
    def view_department(department_id):
        department = department_service.get_department(department_id)
        if not department:
         return render_template('404.html'), 404
        return render_template('departments/view.html', department=department)

    # Search functionality
    @app.route('/search')
    def search():
        filters = {k: v for k, v in request.args.items() if v}
        return render_template('search.html',
                            employees=employee_service.search_employees(filters),
                            departments=employee_service.get_departments())

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        employee_id = request.view_args.get('employee_id') if request.view_args else None
        return render_template('404.html', 
                            path=request.path, 
                            employee_id=employee_id), 404

    @app.errorhandler(500)
    def server_error(error):
        app.logger.error(f"Server Error: {error}")
        return render_template('500.html'), 500