from flask import current_app, render_template, request, redirect, url_for, flash
from models.document_type import DocumentType
from services.employee_service import EmployeeService
from services.department_service import DepartmentService
from flask import send_from_directory
from models.employee import Employee
from database.connection import db
from services.employee_document_service import EmployeeDocumentService
from services.level_service import LevelService
from services.position_service import PositionService
from services.skill_service import SkillService
from models.position import Position
from models.department import Department
from models.level import EmployeeLevel
from models.skill import Skill
from datetime import datetime

# Initialize services
employee_service = EmployeeService()
department_service = DepartmentService()
employee_document_service = EmployeeDocumentService()
level_service = LevelService()
position_service = PositionService()
skill_service = SkillService()

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

    @app.route('/employees/<int:employee_id>')
    def employee_detail(employee_id):
        employee = employee_service.get_employee(employee_id)
        if not employee:
            return render_template('404.html', employee_id=employee_id), 404
        return render_template('employees/details.html', employee=employee)

    @app.route('/employees/add', methods=['GET', 'POST'])
    def add_employee():
        if request.method == 'POST':
            try:
                form_data = request.form
                print("📥 Route received form data:", form_data)

                # Create employee
                employee_id = employee_service.create_employee(form_data)
                
                # Handle document uploads
                if 'document_file[]' in request.files:
                    employee_document_service.save_employee_documents(
                        employee_id=employee_id,
                        form_data=form_data,
                        files=request.files
                    )
                
                flash('Employee added successfully!', 'success')
                return redirect(url_for('list_employees'))
            except Exception as e:
                flash(f'Failed to add employee: {str(e)}', 'error')

        # Load all dropdown options
        positions = position_service.get_all_positions()
        departments = department_service.get_all_departments()
        levels = level_service.get_all_levels()
        document_types = employee_document_service.get_all_document_types()
        certificate_types = employee_document_service.get_all_certificate_types()
        skills = skill_service.get_all_skills()

        return render_template(
            'employees/add.html',
            positions=positions,
            departments=departments,
            levels=levels,
            document_types=document_types,
            certificate_types=certificate_types,
            skills=skills
        )

    @app.route('/employees/edit/<int:employee_id>', methods=['GET', 'POST'])
    @app.route('/employees/edit/<int:employee_id>', methods=['GET', 'POST'])
    def edit_employee(employee_id):
        # Initialize all services with the same db session
        from database.connection import db
        
        employee_service = EmployeeService(db)
        position_service = PositionService(db)
        department_service = DepartmentService(db)
        level_service = LevelService(db)
        skill_service = SkillService(db)
        employee_document_service = EmployeeDocumentService(db)

        # Get employee with all relationships
        employee = employee_service.get_employee(employee_id)
        if not employee:
            flash('Employee not found', 'error')
            return redirect(url_for('list_employees'))

        if request.method == 'POST':
            try:
                form_data = request.form
                
                # First update the employee
                if employee_service.update_employee(employee_id, form_data, request.files):
                    flash('Employee updated successfully!', 'success')
                else:
                    flash('Failed to update employee', 'error')
                
                return redirect(url_for('list_employees'))
                
            except ValueError as ve:
                flash(f'Validation error: {str(ve)}', 'error')
            except Exception as e:
                db.rollback()  # Ensure rollback on error
                flash(f'Error updating employee: {str(e)}', 'error')
                current_app.logger.error(f"Error updating employee {employee_id}: {str(e)}")
            return redirect(request.url)  # Stay on form to show errors

        # GET request - load form with current data
        positions = position_service.get_all_positions()
        departments = department_service.get_all_departments()
        levels = level_service.get_all_levels()
        document_types = employee_document_service.get_all_document_types()
        certificate_types = employee_document_service.get_all_certificate_types()
        skills = skill_service.get_all_skills()
        employee_skill_ids = [s.skill_id for s in employee.skills]

        return render_template(
            'employees/edit.html',
            employee=employee,
            positions=positions,
            departments=departments,
            levels=levels,
            document_types=document_types,
            certificate_types=certificate_types,
            skills=skills,
            employee_skill_ids=employee_skill_ids
        )
    @app.route('/employees/delete/<int:employee_id>', methods=['POST'])
    def delete_employee(employee_id):
        try:
            if employee_service.delete_employee(employee_id):
                flash('Employee deleted successfully!', 'success')
            else:
                flash('Employee not found', 'error')
        except Exception as e:
            flash(f'Error deleting employee: {str(e)}', 'error')
        
        return redirect(url_for('list_employees'))

    # Department routes (maintain original functionality)
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
                return redirect(url_for('list_departments'))
            except ValueError as e:
                flash(str(e), "error")
        return render_template('departments/add.html')

    @app.route('/departments/<int:department_id>')
    def department_detail(department_id):
        department = department_service.get_department(department_id)
        if not department:
            return render_template('404.html'), 404
        return render_template('departments/detail.html', department=department)

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