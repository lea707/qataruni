import uuid
from sqlalchemy.orm import joinedload 
from flask import current_app, jsonify, render_template, request, redirect, url_for, flash
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
from models.employee_document import EmployeeDocument
from models.associations import employee_skills
from flask import session
from werkzeug.utils import secure_filename
import os
from flask import Blueprint
from flask import request, redirect, url_for, flash
from services.file_handler import handle_file_uploads
from services.employee_service import EmployeeService
from pathlib import Path
from urllib.parse import urlencode
import re
from flask import g
from utils.role_helpers import get_director_department_ids

employee_service = EmployeeService()
employee_service = EmployeeService()
department_service = DepartmentService()
employee_document_service = EmployeeDocumentService()
level_service = LevelService()
position_service = PositionService()
skill_service = SkillService()
employee_bp = Blueprint('employee_bp', __name__, url_prefix='/employees')
def init_routes(app):
    @app.route('/static/<path:filename>')
    def static_files(filename):
        response = send_from_directory(app.static_folder, filename)
        if filename.endswith('.css'):
            response.headers['Content-Type'] = 'text/css'
        return response
    
    @app.route('/')
    def home():
        return render_template('index.html')

    @app.route('/about')
    def about():
        return render_template('about.html')
# EMPLOYEES
    def get_director_department_ids():
        # Get the director's department and all sub-departments
        user_role = session.get('role_name')
        user_emp_id = session.get('emp_id')
        if user_role != 'Director' or not user_emp_id:
            return []
        # Find the department where this user is the director
        director_dept = db().query(Department).filter_by(director_emp_id=user_emp_id).first()
        if not director_dept:
            return []
        # Recursively get all sub-department ids
        def get_sub_dept_ids(dept):
            ids = [dept.department_id]
            for sub in db().query(Department).filter_by(parent_department_id=dept.department_id).all():
                ids.extend(get_sub_dept_ids(sub))
            return ids
        return get_sub_dept_ids(director_dept)

    @app.route('/employees')
    def list_employees():
        if has_role('Admin'):
            employees = employee_service.get_all_employees()
        elif has_role('HR'):
            # HR sees employees in their own department
            user_emp_id = session.get('emp_id')
            user_employee = db().query(Employee).filter_by(emp_id=user_emp_id).first()
            if user_employee and user_employee.department_id:
                employees = [e for e in employee_service.get_all_employees() if e.department_id == user_employee.department_id]
            else:
                employees = []
        elif has_role('Director'):
            dept_ids = get_director_department_ids()
            employees = [e for e in employee_service.get_all_employees() if e.department_id in dept_ids]
        elif has_role('Supervisor'):
            # Supervisors see their direct reports AND themselves
            user_emp_id = session.get('emp_id')
            employees = [e for e in employee_service.get_all_employees() if e.supervisor_emp_id == user_emp_id or e.emp_id == user_emp_id]
        else:
            # Regular employees see only themselves
            user_emp_id = session.get('emp_id')
            employees = [e for e in employee_service.get_all_employees() if e.emp_id == user_emp_id]
        return render_template('employees/list.html', employees=employees)

    @app.route('/employees/<int:employee_id>')
    def employee_detail(employee_id):
        employee = employee_service.get_employee(employee_id)
        if not employee:
            flash('Employee not found', 'error')
            return redirect(url_for('list_employees'))
        
        # Get employee skills with metadata
        skills = employee_service.get_employee_skills_with_metadata(employee_id)
        
        return render_template('employees/details.html', 
                             employee=employee, 
                             skills=skills,
                             show_documents=True)
 
    @app.route('/api/check-business-id')
    def check_business_id():
        business_id = request.args.get('id')
        exists = employee_service.business_id_exists(business_id)
        return jsonify({'exists': exists})

    @app.route('/api/skills/search')
    def search_skills():
        query = request.args.get('q', '').strip()
        if len(query) < 2:
            return jsonify([])
        
        try:
            skills = skill_service.search_skills(query)
            return jsonify([{'skill_id': skill.skill_id, 'skill_name': skill.skill_name} for skill in skills])
        except Exception as e:
            current_app.logger.error(f"Error searching skills: {e}")
            return jsonify([])

    @app.route('/api/supervisors/search')
    def search_supervisors():
        query = request.args.get('q', '').strip()
        if len(query) < 2:
            return jsonify([])
        
        try:
            supervisors = employee_service.search_supervisors(query)
            return jsonify([{'emp_id': emp.emp_id, 'name': f"{emp.english_name} ({emp.busness_id})"} for emp in supervisors])
        except Exception as e:
            current_app.logger.error(f"Error searching supervisors: {e}")
            return jsonify([])
    @app.route('/employees/add', methods=['GET', 'POST'])
    def add_employee():
        if not has_role('Admin', 'HR'):
            flash('You do not have permission to add employees.', 'danger')
            return redirect(url_for('list_employees'))
        if request.method == 'POST':
            try:
                employee_id = employee_service.create_employee(request.form, request.files)
                flash("Employee created successfully!", "success")
                return redirect(url_for('list_employees'))
            except Exception as e:
                flash(f"Error creating employee: {str(e)}", "danger")
                return redirect(url_for('add_employee'))
        existing_skills = skill_service.get_all_skills()
        skills_data = [{'skill_id': skill.skill_id, 'skill_name': skill.skill_name} for skill in existing_skills]
        
        return render_template('employees/add.html',
                            positions=position_service.get_all_positions(),
                            departments=department_service.get_all_departments(),
                            employee_levels=level_service.get_all_levels(),
                            skill_categories=skill_service.get_all_skill_categories(),
                            certificate_types=employee_document_service.get_all_certificate_types(),
                            document_types=employee_document_service.get_all_document_types(),
                            existing_skills=skills_data)
    
    @app.route('/employees/edit/<int:employee_id>', methods=['GET', 'POST'])
    def edit_employee(employee_id):
        db_session = db()
        
        try:
            # Check permissions first
            if not has_role('Admin'):
                user_emp_id = session.get('emp_id')
                if has_role('HR'):
                    if employee_id != user_emp_id:
                        flash('Access denied: You can only edit your own profile.', 'danger')
                        return redirect(url_for('list_employees'))
                elif has_role('Director'):
                    dept_ids = get_director_department_ids()
                    target_employee = db_session.query(Employee).filter_by(emp_id=employee_id).first()
                    if not target_employee or target_employee.department_id not in dept_ids:
                        flash('Access denied: You can only edit employees in your department.', 'danger')
                        return redirect(url_for('list_employees'))
                elif employee_id != user_emp_id:
                    flash('Access denied: You can only edit your own profile.', 'danger')
                    return redirect(url_for('list_employees'))

            # Initialize services
            employee_service = EmployeeService(db_session)
            position_service = PositionService()
            department_service = DepartmentService()
            level_service = LevelService()
            skill_service = SkillService()
            employee_document_service = EmployeeDocumentService()

            # Load employee with all relationships
            employee = db_session.query(Employee).options(
                joinedload(Employee.department),
                joinedload(Employee.position),
                joinedload(Employee.level),
                joinedload(Employee.skills),
                joinedload(Employee.documents).joinedload(EmployeeDocument.certificate_type),
                joinedload(Employee.documents).joinedload(EmployeeDocument.document_type)
            ).filter(Employee.emp_id == employee_id).first()
            
            if not employee:
                flash('Employee not found', 'error')
                return redirect(url_for('list_employees'))

            if request.method == 'POST':
                try:
                    if employee_service.update_employee(employee_id, request.form, request.files):
                        flash('Employee updated successfully!', 'success')
                    else:
                        flash('Failed to update employee', 'error')
                    return redirect(url_for('list_employees'))
                except Exception as e:
                    db_session.rollback()
                    flash(f'Error updating employee: {str(e)}', 'error')
                    current_app.logger.error(f"Error updating employee {employee_id}: {str(e)}")

            # Force load relationships while session is open
            documents = [doc for doc in employee.documents]
            employee_skills = employee_service.get_employee_skills_with_metadata(employee_id)

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
                employee_skills=employee_skills,
                employee_documents=documents
            )

        finally:
            db_session.close()
    def has_role(*roles):
        user_role = session.get('role_name')
        return user_role in roles

    def is_director_of_department(employee):
        user_role = session.get('role_name')
        user_emp_id = session.get('emp_id')
        # Only directors can use this
        if user_role != 'Director' or not user_emp_id:
            return False
        # Get the department's director_emp_id
        dept = employee.department
        return dept and dept.director_emp_id == user_emp_id

    @app.route('/employees/deactivate/<int:employee_id>', methods=['POST'])
    def deactivate_employee(employee_id):
        db_session = db()
        try:
            employee = db_session.query(Employee).filter_by(emp_id=employee_id).first()
            if not employee:
                flash('Employee not found', 'error')
                return redirect(url_for('list_employees'))
            # Permission check
            if not (has_role('Admin', 'HR') or is_director_of_department(employee)):
                flash('You do not have permission to deactivate this employee.', 'danger')
                return redirect(url_for('list_employees'))
            employee.is_active = False
            db_session.commit()
            flash('Employee deactivated successfully!', 'success')
        except Exception as e:
            db_session.rollback()
            flash(f'Error deactivating employee: {str(e)}', 'error')
        finally:
            db_session.close()
        return redirect(url_for('list_employees'))

    @app.route('/employees/activate/<int:employee_id>', methods=['POST'])
    def activate_employee(employee_id):
        db_session = db()
        try:
            employee = db_session.query(Employee).filter_by(emp_id=employee_id).first()
            if not employee:
                flash('Employee not found', 'error')
                return redirect(url_for('list_employees'))
            # Permission check
            if not (has_role('Admin', 'HR') or is_director_of_department(employee)):
                flash('You do not have permission to activate this employee.', 'danger')
                return redirect(url_for('list_employees'))
            employee.is_active = True
            db_session.commit()
            flash('Employee activated successfully!', 'success')
        except Exception as e:
            db_session.rollback()
            flash(f'Error activating employee: {str(e)}', 'error')
        finally:
            db_session.close()
        return redirect(url_for('list_employees'))

    @app.route('/employees/delete/<int:employee_id>', methods=['POST'])
    def delete_employee(employee_id):
        if not has_role('HR', 'Admin'):
            flash('You do not have permission to delete employees.', 'danger')
            return redirect(url_for('list_employees'))
        try:
            if employee_service.delete_employee(employee_id):
                flash('Employee deleted successfully!', 'success')
            else:
                flash('Employee not found', 'error')
        except Exception as e:
            flash(f'Error deleting employee: {str(e)}', 'error')
        
        return redirect(url_for('list_employees'))

     # In your Flask route

    @app.route('/upload', methods=['POST'])
    def upload():
        files = request.files.getlist('cv_files')
        parsed_results = []

        for file in files:
            path = os.path.join('uploads', file.filename)
            file.save(path)

        return jsonify(parsed_results)
    @app.route('/documents/download/<int:doc_id>')
    def download_document(doc_id):
        """Download a document file"""
        try:
            from models.employee_document import EmployeeDocument
            document = db().query(EmployeeDocument).get(doc_id)
            
            if not document or not document.file_path:
                flash('Document not found', 'error')
                return redirect(url_for('list_employees'))
            
            file_path = Path(document.file_path)
            if not file_path.exists():
                flash('File not found', 'error')
                return redirect(url_for('list_employees'))
            
            return send_from_directory(
                file_path.parent, 
                file_path.name, 
                as_attachment=True,
                download_name=document.document_name or file_path.name
            )
            
        except Exception as e:
            current_app.logger.error(f"Error downloading document {doc_id}: {e}")
            flash('Error downloading document', 'error')
            return redirect(url_for('list_employees'))

    @app.route('/documents/delete/<int:doc_id>', methods=['POST'])
    def delete_document(doc_id):
        """Delete a document"""
        try:
            from models.employee_document import EmployeeDocument
            session = db()
            document = session.query(EmployeeDocument).get(doc_id)
            
            if not document:
                flash('Document not found', 'error')
                return redirect(url_for('list_employees'))
            
            # Store employee ID for redirect
            employee_id = document.employee_id
            
            # Delete the file if it exists
            if document.file_path:
                try:
                    file_path = Path(document.file_path)
                    if file_path.exists():
                        file_path.unlink()
                        current_app.logger.info(f"Deleted file: {file_path}")
                except Exception as e:
                    current_app.logger.error(f"Failed to delete file {document.file_path}: {e}")
            
            # Delete the database record
            session.delete(document)
            session.commit()
            
            flash('Document deleted successfully!', 'success')
            return redirect(url_for('edit_employee', employee_id=employee_id))
            
        except Exception as e:
            session.rollback()
            current_app.logger.error(f"Error deleting document {doc_id}: {e}")
            flash('Error deleting document', 'error')
            return redirect(url_for('list_employees'))
        finally:
            session.close()

    # Department routes (maintain original functionality)
    @app.route('/departments')
    def list_departments():
        if has_role('Admin'):
            departments = department_service.get_all_departments()
        elif has_role('HR'):
            user_emp_id = session.get('emp_id')
            from models.employee import Employee
            user_employee = db().query(Employee).filter_by(emp_id=user_emp_id).first()
            if user_employee and user_employee.department_id:
                departments = [d for d in department_service.get_all_departments() if d.department_id == user_employee.department_id]
            else:
                departments = []
        elif has_role('Director'):
            dept_ids = get_director_department_ids()
            departments = [d for d in department_service.get_all_departments() if d.department_id in dept_ids]
        else:
            departments = []
        all_employees = employee_service.get_all_employees()
        return render_template('departments/list.html', departments=departments, all_employees=all_employees)

    @app.route('/departments/add', methods=['GET', 'POST'])
    def add_department():
        if request.method == 'POST':
            name = request.form.get('name')
            director_label = request.form.get('director_emp_id')
            parent_department_label = request.form.get('parent_department_id')

            # Map director label to ID
            director_emp_id = None
            if director_label:
                for emp in employee_service.get_all_employees():
                    label = f"{emp.english_name} ({emp.busness_id})"
                    if label == director_label:
                        director_emp_id = emp.emp_id
                        break

            # Map department label to ID
            parent_department_id = None
            if parent_department_label:
                for dept in department_service.get_all_departments():
                    if dept.department_name == parent_department_label:
                        parent_department_id = dept.department_id
                        break

            try:
                # Create the department
                department_id = department_service.create_department(name, director_emp_id=director_emp_id, parent_id=parent_department_id)
                # If a director is selected, update their department and position
                if director_emp_id:
                    from database.connection import db
                    from models.employee import Employee
                    from models.position import Position
                    from models.level import EmployeeLevel
                    session = db() if callable(db) else db
                    try:
                        # Get the Director position_id
                        director_position = session.query(Position).filter(Position.position_name.ilike('Director')).first()
                        if director_position:
                            director_position_id = director_position.position_id
                        else:
                            # If not found, create it
                            director_position = Position(position_name='Director', is_active=True)
                            session.add(director_position)
                            session.commit()
                            director_position_id = director_position.position_id
                        # Get the Director level_id
                        director_level = session.query(EmployeeLevel).filter(EmployeeLevel.level_name.ilike('Director')).first()
                        if director_level:
                            director_level_id = director_level.level_id
                        else:
                            director_level = EmployeeLevel(level_name='Director')
                            session.add(director_level)
                            session.commit()
                            director_level_id = director_level.level_id
                        # Update the employee
                        employee = session.query(Employee).get(int(director_emp_id))
                        if employee:
                            employee.department_id = department_id
                            employee.position_id = director_position_id
                            employee.level_id = director_level_id
                            session.commit()
                    finally:
                        session.close()
                flash(f"Department '{name}' created successfully!", "success")
                return redirect(url_for('list_departments'))
            except ValueError as e:
                flash(str(e), "error")
        # Fetch employees and departments for the form
        all_employees = employee_service.get_all_employees()
        all_departments = department_service.get_all_departments()
        return render_template('departments/add.html', employees=all_employees, departments=all_departments)

    @app.route('/departments/<int:department_id>')
    def department_detail(department_id):
        department = department_service.get_department(department_id)
        if not department:
            return render_template('404.html'), 404
        return render_template('departments/detail.html', department=department)

    @app.route('/departments/edit/<int:department_id>', methods=['GET', 'POST'])
    def edit_department(department_id):
        if not has_role('Admin'):
            flash('Access denied: Only Admin can edit departments.', 'danger')
            return redirect(url_for('list_departments'))
        department = department_service.get_department(department_id)
        if not department:
            flash('Department not found', 'error')
            return redirect(url_for('list_departments'))
        if request.method == 'POST':
            name = request.form.get('name')
            director_emp_id = request.form.get('director_emp_id')
            parent_department_id = request.form.get('parent_department_id')
            try:
                department_service.update_department(
                    department_id,
                    name=name,
                    director_emp_id=director_emp_id or None,
                    parent_department_id=parent_department_id or None
                )
                flash('Department updated successfully!', 'success')
                return redirect(url_for('list_departments'))
            except Exception as e:
                flash(f'Error updating department: {str(e)}', 'error')
        # For GET or failed POST
        all_employees = employee_service.get_all_employees()
        all_departments = department_service.get_all_departments()
        return render_template('departments/edit.html', department=department, employees=all_employees, departments=all_departments)

    @app.route('/departments/delete/<int:department_id>', methods=['POST'])
    def delete_department(department_id):
        if not has_role('Admin'):
            flash('Access denied: Only Admin can delete departments.', 'danger')
            return redirect(url_for('list_departments'))
        try:
            if department_service.delete_department(department_id):
                flash('Department deleted successfully!', 'success')
            else:
                # Check if the department still has employees
                department = department_service.get_department(department_id)
                if department and getattr(department, 'employees', None) and len(department.employees) > 0:
                    flash("You can't delete this department because it still has employees.", 'error')
                else:
                    flash('Department not found', 'error')
        except Exception as e:
            flash(f'Error deleting department: {str(e)}', 'error')
        return redirect(url_for('list_departments'))

    @app.route('/search', methods=['GET'])
    def search():
        # Extract search parameters from query string
        search_employee_query = request.args.get('employee_query', '').strip()
        search_skill_query = request.args.get('skill_query', '').strip()
        search_business_id = request.args.get('business_id', '').strip()
        search_name = request.args.get('name', '').strip()
        search_department = request.args.get('department', '').strip()
        search_skill_name = search_skill_query or request.args.get('skill_name', '').strip()
        search_skill_category = request.args.get('skill_category', '').strip()
        search_skill_level = request.args.get('skill_level', '').strip()
        search_certificate_type = request.args.get('certificate_type', '').strip()
        search_document_type = request.args.get('document_type', '').strip()
        search_supervisor_emp_id = request.args.get('supervisor_emp_id', '').strip()
        search_position_id = request.args.get('position_id', '').strip()
        search_hire_date_from = request.args.get('hire_date_from', '').strip()
        search_hire_date_to = request.args.get('hire_date_to', '').strip()
        sort_by = request.args.get('sort_by', '').strip()

        # If employee_query is provided, use it for name or business_id
        if search_employee_query:
            import re
            match = re.search(r'\(([^)]+)\)', search_employee_query)
            if match:
                search_business_id = match.group(1).strip()
                search_name = ''
            elif '-' in search_employee_query:
                search_business_id = search_employee_query.strip()
                search_name = ''
            else:
                search_name = search_employee_query.strip()
                search_business_id = ''

        # Get all departments for the dropdown
        departments = [dept.department_name for dept in department_service.get_all_departments()]
        # Set allowed_departments based on role
        if has_role('Director'):
            dept_ids = get_director_department_ids()
            g.allowed_departments = [d.department_name for d in department_service.get_all_departments() if d.department_id in dept_ids]
        elif has_role('HR'):
            # HR can only see their own department
            user_emp_id = session.get('emp_id')
            user_employee = db().query(Employee).filter_by(emp_id=user_emp_id).first()
            if user_employee and user_employee.department_id:
                user_dept = db().query(Department).filter_by(department_id=user_employee.department_id).first()
                g.allowed_departments = [user_dept.department_name] if user_dept else []
            else:
                g.allowed_departments = []
        else:
            g.allowed_departments = departments
        existing_skills = [{'skill_id': skill.skill_id, 'skill_name': skill.skill_name} for skill in skill_service.get_all_skills()]
        skill_categories = skill_service.get_all_skill_categories()
        certificate_types = employee_document_service.get_all_certificate_types()
        document_types = employee_document_service.get_all_document_types()
        positions = position_service.get_all_positions()

        # Get all employees for datalists
        all_employees = employee_service.get_all_employees()
        # Show all employees if no filters are selected
        employees = employee_service.search_employees(
            business_id=search_business_id,
            name=search_name,
            department=search_department,
            skill_name=search_skill_name,
            skill_category=search_skill_category,
            skill_level=search_skill_level,
            certificate_type=search_certificate_type,
            document_type=search_document_type,
            supervisor_emp_id=search_supervisor_emp_id,
            position_id=search_position_id,
            hire_date_from=search_hire_date_from,
            hire_date_to=search_hire_date_to,
            sort_by=sort_by
        )
        # Restrict search results by role
        if has_role('Director'):
            dept_ids = get_director_department_ids()
            # Map allowed department IDs to names
            allowed_dept_names = [d.department_name for d in department_service.get_all_departments() if d.department_id in dept_ids]
            employees = [e for e in employees if e['department'] in allowed_dept_names]
        elif has_role('HR'):
            # HR sees employees in their own department
            user_emp_id = session.get('emp_id')
            user_employee = db().query(Employee).filter_by(emp_id=user_emp_id).first()
            if user_employee and user_employee.department_id:
                user_dept = db().query(Department).filter_by(department_id=user_employee.department_id).first()
                if user_dept:
                    employees = [e for e in employees if e['department'] == user_dept.department_name]
                else:
                    employees = []
            else:
                employees = []
        elif has_role('Supervisor'):
            # Supervisors see their direct reports AND themselves
            user_emp_id = session.get('emp_id')
            employees = [e for e in employees if e['supervisor_emp_id'] == user_emp_id or e['emp_id'] == user_emp_id]
        elif not has_role('Admin'):
            user_emp_id = session.get('emp_id')
            employees = [e for e in employees if e['emp_id'] == user_emp_id]
        # Pagination
        page = int(request.args.get('page', 1))
        page_size = 10
        total_employees = len(employees)
        total_pages = (total_employees + page_size - 1) // page_size
        start = (page - 1) * page_size
        end = start + page_size
        paginated_employees = employees[start:end]
        args_for_pagination = request.args.to_dict()
        if 'page' in args_for_pagination:
            args_for_pagination.pop('page')
        query_string = urlencode(args_for_pagination)
        # Convert all_employees to a list of dicts for JSON serialization
        all_employees_dicts = [
            {
                'emp_id': emp.emp_id,
                'english_name': emp.english_name,
                'arab_name': emp.arab_name,
                'busness_id': emp.busness_id,
                'department_name': emp.department.department_name if emp.department else '',
            }
            for emp in all_employees
        ]
        return render_template('search.html',
            employees=paginated_employees,
            departments=departments,
            existing_skills=existing_skills,
            skill_categories=skill_categories,
            certificate_types=certificate_types,
            document_types=document_types,
            positions=positions,
            all_employees=all_employees_dicts,
            total_pages=total_pages,
            page=page,
            query_string=request.query_string.decode('utf-8'),
            request=request,
            g=g
        )

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