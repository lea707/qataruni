import uuid
from flask import current_app, render_template, request, redirect, url_for, flash
from database.repositories.skill_category_repository import SkillCategoryRepository
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
from models.employee import Employee
from models.associations import employee_skills
from flask import session

   
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
        skills = employee_service.get_employee_skills_with_metadata(employee_id)

        user_role = session.get('user_role')  # or however you're storing it

        show_documents = user_role in ['Admin', 'HR']

        return render_template(
            "employees/details.html",
            employee=employee,
            skills=skills,
            show_documents=show_documents
        )

    @app.route('/employees/add', methods=['GET', 'POST'])
    def add_employee():
        if request.method == 'POST':
            print("🔁 POST request received at /employees/add")
            print("📄 Form data:", request.form)
            print("📎 Files received:", request.files)

            try:
                employee_service.create_employee(request.form, request.files)
                print("✅ Employee creation completed")
                flash("Employee added successfully!", "success")
                return redirect(url_for('list_employees'))
            except Exception as e:
                print("❌ Error during employee creation:", str(e))
                flash(f"Error adding employee: {str(e)}", "danger")
                return redirect(url_for('add_employee'))

        # GET request — load form options
        print("📥 GET request to load Add Employee form")
        return render_template(
            'employees/add.html',
            positions=position_service.get_all_positions(),
            departments=department_service.get_all_departments(),
            levels=level_service.get_all_levels(),
            document_types=employee_document_service.get_all_document_types(),
            certificate_types=employee_document_service.get_all_certificate_types(),
            skills=skill_service.get_all_skills(),
            skill_categories=skill_service.get_all_skill_categories(),
            employee_skills=level_service.get_all_levels()
        )

    @app.route('/employees/edit/<int:employee_id>', methods=['GET', 'POST'])
  
    @app.route('/employees/edit/<int:employee_id>', methods=['GET', 'POST'])
    @app.route('/employees/edit/<int:employee_id>', methods=['GET', 'POST'])
    def edit_employee(employee_id):
        db_session = db()
        employee_service = EmployeeService(db_session)
        
        try:
            employee = employee_service.get_employee(employee_id)
            if not employee:
                flash('Employee not found', 'error')
                return redirect(url_for('list_employees'))

            if request.method == 'POST':
                try:
                    form_data = request.form.to_dict()
                    form_data['is_active'] = 'is_active' in request.form
                    
                    if employee_service.update_employee(employee_id, form_data, request.files):
                        flash('Employee updated successfully!', 'success')
                    else:
                        flash('Failed to update employee', 'error')
                    return redirect(url_for('list_employees'))
                except Exception as e:
                    db_session.rollback()
                    flash(f'Error updating employee: {str(e)}', 'error')
                    current_app.logger.error(f"Error updating employee {employee_id}: {str(e)}")

            # GET request - load form with current data
            position_service = PositionService()
            department_service = DepartmentService()
            level_service = LevelService()
            skill_service = SkillService()
            employee_document_service = EmployeeDocumentService()

            return render_template(
                'employees/edit.html',
                employee=employee,
                positions=position_service.get_all_positions(),
                departments=department_service.get_all_departments(),
                levels=level_service.get_all_levels(),
                document_types=employee_document_service.get_all_document_types(),
                certificate_types=employee_document_service.get_all_certificate_types(),
                skills=skill_service.get_all_skills(),
                skill_categories=skill_service.get_all_skill_categories(),
                employee_skills=employee_service.get_employee_skills_with_metadata(employee_id)
            )

        finally:
            db_session.close()

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