#
# This file contains the URL routes for the Employee Skills Tracker application.
# It defines how the application responds to different URL paths.
#

import uuid
from sqlalchemy.orm import joinedload 
from flask import current_app, jsonify, render_template, request, redirect, url_for, flash
from database.repositories.skill_category_repository import SkillCategoryRepository
from services.excel_reader import ExcelEmployeeReader
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
department_service = DepartmentService()
employee_document_service = EmployeeDocumentService()
level_service = LevelService()
position_service = PositionService()
skill_service = SkillService()
employee_bp = Blueprint('employee_bp', __name__, url_prefix='/employees')
UPLOAD_FOLDER = 'profiles/uploaded'
ALLOWED_EXTENSIONS = {'xlsx'}

def init_routes(app):
    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    def has_role(*roles):
        user_role = session.get('role_name')
        return user_role in roles



    @app.route('/')
    def home():
        return render_template('index.html')

    @app.route('/about')
    def about():
        return render_template('about.html')

    @app.route('/static/<path:filename>')
    def static_files(filename):
        response = send_from_directory(app.static_folder, filename)
        if filename.endswith('.css'):
            response.headers['Content-Type'] = 'text/css'
        return response

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
        employees = sorted(employees, key=lambda e: e.busness_id or "")
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
                    # Update employee with form data and files
                    success = employee_service.update_employee(employee_id, request.form, request.files)
                    if success:
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

    @app.route('/upload', methods=['GET', 'POST'])
    def upload_file():
        if request.method == 'GET':
            return render_template('upload.html')
            
        print("start uploading file")
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        print(f"uploads folder {UPLOAD_FOLDER}")
        
        if 'documents' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        files = request.files.getlist('documents')
        if not files or all(file.filename == '' for file in files):
            return jsonify({'error': 'No selected file'}), 400
        
        processed_files = []
        for file in files:
            if file.filename != '' and allowed_file(file.filename):
                try:
                    original_name = file.filename
                    extension = Path(original_name).suffix
                    safe_name = secure_filename(original_name)
                    
                    # Save once with UUID
                    temp_path = os.path.join(UPLOAD_FOLDER, f"temp_{uuid.uuid4()}{extension}")
                    file.save(temp_path)

                    # Check it’s not empty
                    if os.path.getsize(temp_path) == 0:
                        raise ValueError(f"Uploaded file {original_name} is empty")
                    
                    # Process the file - only Excel files supported
                    if extension.lower() == ".xlsx":
                        print("__________inside process excel______")
                        result = ExcelEmployeeReader.import_employees(temp_path, update_existing=True)
                    else:
                        # Non-Excel files are not supported
                        result = None
                        current_app.logger.warning(f"File type {extension} not supported. Only Excel files (.xlsx) are processed.")


                    if result:
                        processed_files.append({
                            'filename': safe_name,
                            'result': result
                        })
                    
                    # Clean up
                    os.remove(temp_path)
                
                except Exception as e:
                    current_app.logger.error(f"Error processing uploaded file {file.filename}: {str(e)}")
                    return jsonify({'error': f'Error processing {file.filename}: {str(e)}'}), 500
            else:
                return jsonify({'error': f'File type not allowed: {file.filename}'}), 400
        
        if processed_files:
            flash(f"Successfully processed {len(processed_files)} file(s).", "success")
            return redirect(url_for('upload_file'))
        else:
            flash("No files were successfully processed.", "danger")
            return redirect(url_for('upload_file'))


    @app.route('/documents/download/<int:doc_id>')
    def download_document(doc_id):
        doc = employee_document_service.get_document(doc_id)
        if not doc or not os.path.exists(doc.file_path):
            flash('Document not found.', 'danger')
            return redirect(request.referrer or url_for('home'))

        directory, filename = os.path.split(doc.file_path)
        return send_from_directory(directory, filename, as_attachment=True)

    @app.route('/documents/delete/<int:doc_id>', methods=['POST'])
    def delete_document(doc_id):
        doc = employee_document_service.get_document(doc_id)
        if doc:
            emp_id = doc.employee_id
            if employee_document_service.delete_document(doc_id):
                flash('Document deleted successfully.', 'success')
            else:
                flash('Error deleting document.', 'danger')
            return redirect(url_for('edit_employee', employee_id=emp_id))
        else:
            flash('Document not found.', 'danger')
            return redirect(url_for('home'))

    @app.route("/departments")
    def list_departments():
        departments = department_service.get_all_departments()
        employees = employee_service.get_all_employees()
  
        return render_template(
            "departments/list.html",
            departments=departments,
            all_employees=employees
        )

    @app.route('/departments/add', methods=['GET', 'POST'])
    def add_department():
            if request.method == 'POST':
                name = request.form.get('department_name')  # safe getter
                department_service.create_department(name)
                flash("Department added successfully!", "success")
                return redirect(url_for('list_departments'))
            return render_template(
                "departments/add.html",
                employees=employee_service.get_all_employees(),
                departments=department_service.get_all_departments()
            )



    @app.route('/departments/<int:department_id>')
    def department_detail(department_id):
        department = department_service.get_department(department_id)
        if not department:
            flash('Department not found', 'error')
            return redirect(url_for('list_departments'))
        return render_template('departments/details.html', department=department)

    @app.route("/departments/<int:department_id>/edit", methods=["GET", "POST"])
    def edit_department(department_id):
        print(f"[ROUTE] edit_department called with department_id={department_id}")

        department = department_service.get_department(department_id)
        if not department:
            print("[ROUTE] Department not found.")
            flash("Department not found.", "danger")
            return redirect(url_for("list_departments"))

        if request.method == "POST":
            print("[ROUTE] Received POST request")
            print("DEBUG: request.form =", request.form)

            new_name = request.form.get("department_name")
            new_director_id = request.form.get("director_emp_id")

            print(f"DEBUG: new_name={new_name}, new_director_id={new_director_id}")

            try:
                # --- Step 1: Handle Director Reassignment ---
                if new_director_id and str(new_director_id).isdigit():
                    print(f"[ROUTE] Processing new director with id={new_director_id}")
                    new_director = employee_service.get_employee(int(new_director_id))
                    print(f"DEBUG: fetched new_director={new_director}")

                    if new_director:
                        if department.director_emp_id and department.director_emp_id != new_director.emp_id:
                            old_director = employee_service.get_employee(department.director_emp_id)
                            print(f"[ROUTE] Found old director: {old_director}")

                            if old_director:
                                print("[ROUTE] Moving old director to Unassigned")
                                employee_service.update_employee(
                                    old_director.emp_id,
                                    {
                                        "department_id": 57,  # Unassigned dept
                                        "position_id": None
                                    }
                                )

                        print("[ROUTE] Assigning new director position")
                        director_position = position_service.get_or_create_position("Director", department.department_id)
                        print(f"DEBUG: director_position={director_position}")

                        employee_service.update_employee(
                            new_director.emp_id,
                            {
                                "department_id": department.department_id,
                                "position_id": director_position.position_id
                            }
                        )

                        print("[ROUTE] Updating department record")
                        department_service.update_department(
                            department_id,
                            name=new_name,
                            director_emp_id=new_director.emp_id
                        )
                    else:
                        print("[ROUTE] new_director was None")

                else:
                    print("[ROUTE] No director change, only updating name")
                    department_service.update_department(department_id, name=new_name)

                flash("Department updated successfully.", "success")
                print("[ROUTE] Department update complete, redirecting")
                return redirect(url_for("department_detail", department_id=department_id))

            except Exception as e:
                print(f"[ROUTE] Exception: {str(e)}")
                flash(f"Error updating department: {str(e)}", "danger")

        # GET request -> render edit form
        print("[ROUTE] GET request - rendering edit form")
        employees = employee_service.get_all_employees()
        return render_template(
            "departments/edit.html",
            department=department,
            employees=employees
        )


    @app.route('/departments/delete/<int:department_id>', methods=['POST'])
    def delete_department(department_id):
        if department_service.delete_department(department_id):
            flash('Department deleted successfully!', 'success')
        else:
            flash('Department not found or could not be deleted', 'error')
        return redirect(url_for('list_departments'))

    @app.route('/search')
    def search():
        page = request.args.get('page', 1, type=int)
        query_dict = request.args.to_dict()
        query_dict.pop('page', None)

        employees = employee_service.search_employees(
            business_id=query_dict.get('business_id'),
            name=query_dict.get('name'),
            department=query_dict.get('department'),
            skill_name=query_dict.get('skill_name'),
            skill_category=query_dict.get('skill_category'),
            skill_level=query_dict.get('skill_level'),
            certificate_type=query_dict.get('certificate_type'),
            document_type=query_dict.get('document_type'),
            supervisor_emp_id=query_dict.get('supervisor_emp_id'),
            position_id=query_dict.get('position_id'),
            hire_date_from=query_dict.get('hire_date_from'),
            hire_date_to=query_dict.get('hire_date_to'),
            sort_by=query_dict.get('sort_by'),
            sort_order=query_dict.get('sort_order')
        )

        all_employees_dicts = [
            {
                'emp_id': emp['emp_id'],
                'english_name': emp['name'].split(' (')[0] if ' (' in emp['name'] else emp['name'],
                'arab_name': emp['name'].split(' (')[1].replace(')', '') if ' (' in emp['name'] else '',
                'busness_id': emp['business_id'],
                'department_name': emp['department']
            }
            for emp in employees
        ]

        from math import ceil
        per_page = 10
        total_pages = ceil(len(employees) / per_page)
        paginated_employees = employees[(page - 1) * per_page: page * per_page]

        department_service = DepartmentService()
        skill_service = SkillService()
        employee_document_service = EmployeeDocumentService()
        position_service = PositionService()

        departments = department_service.get_all_departments()
        existing_skills = skill_service.get_all_skills_serializable(include_category=True)
        skill_categories = skill_service.get_all_skill_categories()
        certificate_types = employee_document_service.get_all_certificate_types()
        document_types = employee_document_service.get_all_document_types()
        positions = position_service.get_all_positions()

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
            query_string=urlencode(query_dict),
            request=request,
            g=g
        )

    @app.errorhandler(404)
    def not_found(error):
        employee_id = request.view_args.get('employee_id') if request.view_args else None
        return render_template('404.html',
                            path=request.path,
                            employee_id=employee_id), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html', error=error), 500
