import uuid
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
    @app.route('/employees')
    def list_employees():
        employees = employee_service.get_all_employees()
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
        employee_service = EmployeeService(db_session)
        
        try:
            # Load employee with all relationships eagerly
            from sqlalchemy.orm import joinedload
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
                    # Use request.form directly to preserve array structure
                    form_data = request.form
                    
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
                employee_skills=employee_service.get_employee_skills_with_metadata(employee_id),
                employee_documents=employee.documents
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