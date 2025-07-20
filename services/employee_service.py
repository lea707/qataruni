import uuid
from flask import current_app, session
from database.repositories.employee_repository import EmployeeRepository
from database.repositories.position_repository import PositionRepository
from database.repositories.skill_repository import SkillRepository
from datetime import datetime
from database.connection import db
from models import skill
from models.employee import Employee
from models.skill import Skill
from models.employee_document import EmployeeDocument
from sqlalchemy import text
from sqlalchemy.orm import joinedload
from models.associations import employee_skills

from pathlib import Path
import os
from werkzeug.utils import secure_filename
from models.certificate_type import CertificateType
from models.document_type import DocumentType

class EmployeeService:
    def __init__(self, db_session=None):
        self.db = db_session if db_session is not None else db
        self.repository = EmployeeRepository()

    def _prepare_employee_data(self, form_data, session):
        is_active = 'is_active' in form_data
        try:
            return {
                'english_name': form_data.get('english_name'),
                'arab_name': form_data.get('arab_name'),
                'email': form_data.get('email'),
                'phone': form_data.get('phone'),
                'position_id': int(form_data.get('position_id')),
                'department_id': int(form_data.get('department_id')),
                'level_id': int(form_data.get('level_id')),
                'hire_date': datetime.strptime(form_data.get('hire_date'), '%Y-%m-%d').date(),
                'supervisor_emp_id': int(form_data['supervisor_emp_id']) if form_data.get('supervisor_emp_id') else None,
                'busness_id': self.repository._generate_business_id(session),
                'is_active': is_active ,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
        except Exception as e:
            current_app.logger.error(f"Error preparing employee data: {e}")
            raise
    
    def create_employee(self, form_data, files=None):
        session = self.db() if callable(self.db) else self.db
        temp_files = [] 
        
        try:
            # Check for duplicate email before creating employee
            existing_employee = session.query(Employee).filter_by(email=form_data.get('email')).first()
            if existing_employee:
                raise RuntimeError(f"An employee with email {form_data.get('email')} already exists.")

            business_id = form_data.get('business_id')
            if not business_id:
                business_id = self._generate_business_id()
            employee = Employee(
                english_name=form_data.get('english_name'),
                arab_name=form_data.get('arab_name'),
                email=form_data.get('email'),
                phone=form_data.get('phone'),
                hire_date=datetime.strptime(form_data.get('hire_date'), '%Y-%m-%d').date(),
                position_id=int(form_data.get('position_id')),
                department_id=int(form_data.get('department_id')),
                level_id=int(form_data.get('level_id')) if form_data.get('level_id') else None,
                supervisor_emp_id=int(form_data.get('supervisor_emp_id')) if form_data.get('supervisor_emp_id') else None,
                is_active='is_active' in form_data,
                busness_id=business_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            session.add(employee)
            session.flush() 
            self._process_employee_skills(form_data, employee.emp_id, session)
            if files:
                current_app.logger.info(f"Processing documents for employee {employee.emp_id} with business_id: {employee.busness_id}")
                temp_files = self._process_employee_documents(form_data, files, employee.emp_id, employee.busness_id, session)
            
            session.commit()
            return employee.emp_id
            
        except Exception as e:
            session.rollback()
            if temp_files:
                self._cleanup_temp_files(temp_files)
            current_app.logger.error(f"Employee creation failed: {e}")
            raise RuntimeError(f"Could not create employee: {e}")
        finally:
            if callable(self.db):
                session.close()
    
    def _prepare_skills_data(self, form_data):
        """Handle both MultiDict and regular dict for skill data"""
        skills = []
        
        if hasattr(form_data, 'getlist'):
            skill_names = form_data.getlist('skill_name[]')
            skill_categories = form_data.getlist('skill_category[]')
            skill_levels = form_data.getlist('skill_level[]')
            
            skills = [{
                'name': name,
                'category': cat,
                'level': level
            } for name, cat, level in zip(skill_names, skill_categories, skill_levels)]
        else:
            if form_data.get('skill_name[]'):
                skills = [{
                    'name': form_data.get('skill_name[]'),
                    'category': form_data.get('skill_category[]'),
                    'level': form_data.get('skill_level[]')
                }]
        
        return skills

    def get_all_employees(self):
        return self.repository.get_all_employees()

    def get_employee(self, employee_id):
        """Get employee details by ID"""
        try:
            employee = self.repository.get_employee(employee_id)
            if not employee:
                raise ValueError("Employee not found")
            return employee
        except Exception as e:
            current_app.logger.error(f"Error getting employee: {e}")
            raise

    def delete_employee(self, employee_id: int) -> bool:
        """Delete an employee by ID with proper cleanup"""
        session = self.db() if callable(self.db) else self.db
        should_close = callable(self.db)
        
        try:
            # Get employee with all relationships
            employee = session.query(Employee).options(
                joinedload(Employee.documents),
                joinedload(Employee.skills)
            ).filter_by(emp_id=employee_id).first()
            
            if not employee:
                return False
            
            # Store business_id for folder cleanup
            business_id = employee.busness_id
            
            # Delete associated documents and their files
            for document in employee.documents:
                if document.file_path:
                    try:
                        file_path = Path(document.file_path)
                        if file_path.exists():
                            file_path.unlink()
                            current_app.logger.info(f"Deleted file: {file_path}")
                    except Exception as e:
                        current_app.logger.error(f"Failed to delete file {document.file_path}: {e}")
                session.delete(document)
            
            # Clear skill associations
            employee.skills.clear()
            
            # Delete the employee
            session.delete(employee)
            session.commit()
            
            # Clean up the employee's document folder
            try:
                employee_folder = Path('employee_documents') / business_id
                if employee_folder.exists():
                    import shutil
                    shutil.rmtree(employee_folder)
                    current_app.logger.info(f"Deleted employee folder: {employee_folder}")
            except Exception as e:
                current_app.logger.error(f"Failed to delete employee folder {employee_folder}: {e}")
            
            return True
            
        except Exception as e:
            if should_close:
                session.rollback()
            current_app.logger.error(f"Error deleting employee {employee_id}: {e}")
            return False
        finally:
            if should_close:
                session.close()

    def update_employee(self, employee_id, form_data, files=None):
        session = self.db() if callable(self.db) else self.db
        temp_files = []  # Track temporary files for cleanup
        
        try:
            employee = session.query(Employee).get(employee_id)
            if not employee:
                return False

            # Check for duplicate email (exclude current employee)
            new_email = form_data.get('email')
            if new_email:
                existing_employee = session.query(Employee).filter(
                    Employee.email == new_email,
                    Employee.emp_id != employee_id
                ).first()
                if existing_employee:
                    raise RuntimeError(f"An employee with email {new_email} already exists.")

            # Update basic fields
            employee.english_name = form_data.get('english_name')
            employee.arab_name = form_data.get('arab_name')
            employee.email = form_data.get('email')
            employee.phone = form_data.get('phone')
            employee.hire_date = datetime.strptime(form_data['hire_date'], '%Y-%m-%d').date()
            employee.position_id = int(form_data['position_id'])
            employee.department_id = int(form_data['department_id'])
            employee.level_id = int(form_data.get('level_id', 0)) or None
            employee.supervisor_emp_id = int(form_data.get('supervisor_emp_id', 0)) or None
            employee.is_active = form_data.get('is_active') == 'true'
            employee.updated_at = datetime.now()

            # Process skills using the same session
            self._process_employee_skills(form_data, employee_id, session)
            
            # Process new documents if files are provided
            if files:
                current_app.logger.info(f"Processing new documents for employee {employee_id}")
                temp_files = self._process_employee_documents(form_data, files, employee_id, employee.busness_id, session)

            session.commit()
            return True

        except Exception as e:
            session.rollback()
            # Clean up any temporary files if update failed
            if temp_files:
                self._cleanup_temp_files(temp_files)
            current_app.logger.error(f"Employee update failed: {e}")
            raise RuntimeError(f"Could not update employee: {e}")
        finally:
            if callable(self.db):
                session.close()
   
    def _process_employee_skills(self, form_data, employee_id: int, session=None) -> None:
        if session is None:
            session = self.db() if callable(self.db) else self.db
            should_close = True
        else:
            should_close = False
        try:
            certified_indices = form_data.getlist('certified[]')
            current_app.logger.info(f"Processing skills for employee {employee_id}")
            current_app.logger.info(f"Certified indices: {certified_indices}")
            # Clear existing skills
            session.execute(
                employee_skills.delete().where(employee_skills.c.employee_id == employee_id)
            )
            # Extract skill data
            skill_names = form_data.getlist('skill_name[]')
            skill_categories = form_data.getlist('skill_category[]')
            skill_levels = form_data.getlist('skill_level[]')
            current_app.logger.info(f"Skill names: {skill_names}")
            current_app.logger.info(f"Skill categories: {skill_categories}")
            current_app.logger.info(f"Skill levels: {skill_levels}")
            for idx, (name, category, level) in enumerate(zip(skill_names, skill_categories, skill_levels)):
                name = name.strip()
                if not name:
                    current_app.logger.info(f"Skipping empty skill name at index {idx}")
                    continue
                # Fix: ensure certified is set to True/1 if checked
                is_certified = name in certified_indices
                current_app.logger.info(f"Skill '{name}' at index {idx}: is_certified={is_certified} (certified_indices={certified_indices})")

                skill = session.query(Skill).filter_by(skill_name=name).first()
                if not skill:
                    skill = Skill(
                        skill_name=name,
                        category_id=int(category) if category and category != "select category" else None
                    )
                    session.add(skill)
                    session.flush()
                    current_app.logger.info(f"Created new skill: {skill.skill_id}")
                
                session.execute(employee_skills.insert().values(
                    employee_id=employee_id,
                    skill_id=skill.skill_id,
                    skill_level=level if level and level != "select level" else None,
                    certified=1 if is_certified else 0
                ))
                current_app.logger.info(f"Associated skill {skill.skill_id} with employee {employee_id}, certified={1 if is_certified else 0}")
            if should_close:
                session.commit()
        except Exception as e:
            if should_close:
                session.rollback()
            current_app.logger.error(f"Error processing employee skills: {e}")
            raise
        finally:
            if should_close and callable(self.db):
                session.close()

    def _process_employee_documents(self, form_data, files, employee_id: int, business_id: str, session=None) -> list:
        """Process employee documents within the same transaction. Returns list of saved file paths for cleanup."""
        if session is None:
            session = self.db() if callable(self.db) else self.db
            should_close = True
        else:
            should_close = False
            
        saved_files = []  # Track all saved files for potential cleanup
        
        try:
            # Create folder structure: employee_documents/business_id/certificates and documents
            base_path = Path('employee_documents')
            employee_folder = base_path / business_id
            certificates_folder = employee_folder / 'certificates'
            documents_folder = employee_folder / 'documents'
            
            current_app.logger.info(f"Creating folders for business_id: {business_id}")
            current_app.logger.info(f"Employee folder: {employee_folder}")
            current_app.logger.info(f"Certificates folder: {certificates_folder}")
            current_app.logger.info(f"Documents folder: {documents_folder}")
            
            # Create directories
            certificates_folder.mkdir(parents=True, exist_ok=True)
            documents_folder.mkdir(parents=True, exist_ok=True)
            
            # Track file names to handle duplicates
            used_certificate_names = set()
            used_document_names = set()
            
            # Process certificate files
            certified_indices = form_data.getlist('certified[]') if hasattr(form_data, 'getlist') else []
            current_app.logger.info(f"Certified indices: {certified_indices}")
            current_app.logger.info(f"Available files: {list(files.keys()) if hasattr(files, 'keys') else 'No files'}")
            
            # Find all certificate files first
            certificate_files = {}
            for key in files.keys():
                if key.startswith('document_file_') and key.endswith('[]'):
                    # Extract the index from the key (e.g., 'document_file_1[]' -> 1)
                    try:
                        file_index = int(key.replace('document_file_', '').replace('[]', ''))
                        certificate_files[file_index] = files[key]
                        current_app.logger.info(f"Found certificate file at index {file_index}: {key}")
                    except ValueError:
                        continue
            
            # Extract skill names for certificate association
            skill_names = form_data.getlist('skill_name[]') if hasattr(form_data, 'getlist') else []

            for idx, is_certified in enumerate(certified_indices):
                if is_certified:
                    current_app.logger.info(f"Processing certified skill at index {idx}")
                    
                    # Look for the file at this index
                    file = certificate_files.get(idx)
                    if file:
                        current_app.logger.info(f"Found file for certified skill at index {idx}")
                    else:
                        current_app.logger.warning(f"No file found for certified skill at index {idx}")
                        continue
                    
                    if file and file.filename:
                        current_app.logger.info(f"Processing file: {file.filename}")
                        cert_type_id = form_data.getlist('certificate_type_id[]')[idx] if hasattr(form_data, 'getlist') else form_data.get('certificate_type_id[]')
                        cert_type = session.query(CertificateType).get(int(cert_type_id)) if cert_type_id else None
                        cert_type_name = self._get_certificate_type_name(session, cert_type_id)
                        current_app.logger.info(f"Certificate type: {cert_type_name}")
                        
                        # Generate filename based on certificate type
                        filename = self._generate_unique_filename(
                            cert_type_name, 
                            file.filename, 
                            certificates_folder, 
                            used_certificate_names
                        )
                        current_app.logger.info(f"Generated filename: {filename}")
                        
                        file_path = certificates_folder / filename
                        file.save(file_path)
                        current_app.logger.info(f"File saved to: {file_path}")
                        saved_files.append(file_path)  # Track for cleanup
                        
                        # Save certificate record
                        issuing_org = (
                            (form_data.getlist('issuing_organization[]')[idx] if hasattr(form_data, 'getlist') else form_data.get('issuing_organization[]'))
                            or (cert_type.default_issuing_org if cert_type else None)
                        )
                        validity_months = (
                            (form_data.getlist('validity_period_months[]')[idx] if hasattr(form_data, 'getlist') else form_data.get('validity_period_months[]'))
                            or (cert_type.default_validity_months if cert_type else None)
                        )
                        document = EmployeeDocument(
                            employee_id=employee_id,
                            cert_type_id=int(cert_type_id) if cert_type_id else None,
                            doc_type_id=None,  # Explicitly set to None for certificates
                            document_name=filename,  # Use the filename as document name
                            file_path=str(file_path),
                            upload_date=datetime.utcnow().date(),
                            skill_name=skill_names[idx] if idx < len(skill_names) else None,
                            issuing_organization=issuing_org,
                            validity_period_months=validity_months
                        )
                        session.add(document)
            
            # Process general documents
            general_files = files.getlist('general_document_file[]') if hasattr(files, 'getlist') else []
            doc_type_ids = form_data.getlist('general_document_type_id[]') if hasattr(form_data, 'getlist') else []
            
            for file, doc_type_id in zip(general_files, doc_type_ids):
                if file and file.filename:
                    # Get document type name
                    doc_type_name = self._get_document_type_name(session, doc_type_id)
                    
                    # Generate filename based on document type
                    filename = self._generate_unique_filename(
                        doc_type_name, 
                        file.filename, 
                        documents_folder, 
                        used_document_names
                    )
                    
                    file_path = documents_folder / filename
                    file.save(file_path)
                    saved_files.append(file_path)  # Track for cleanup
                    
                    document = EmployeeDocument(
                        employee_id=employee_id,
                        doc_type_id=int(doc_type_id) if doc_type_id else None,
                        cert_type_id=None,  # General documents don't have certificate types
                        document_name=filename,  # Use the filename as document name
                        file_path=str(file_path),
                        upload_date=datetime.utcnow().date()
                    )
                    session.add(document)
                    
        except Exception as e:
            if should_close:
                session.rollback()
            # Clean up any files that were saved before the error
            if saved_files:
                self._cleanup_temp_files(saved_files)
            raise RuntimeError(f"Document processing failed: {str(e)}")
        finally:
            if should_close and callable(self.db):
                session.close()
        
        return saved_files

    def _get_certificate_type_name(self, session, cert_type_id):
        """Get certificate type name by ID"""
        if not cert_type_id:
            return "Unknown_Certificate"
        
        cert_type = session.query(CertificateType).get(int(cert_type_id))
        return cert_type.type_name if cert_type else "Unknown_Certificate"
    
    def _get_document_type_name(self, session, doc_type_id):
        """Get document type name by ID"""
        if not doc_type_id:
            return "Unknown_Document"
        
        doc_type = session.query(DocumentType).get(int(doc_type_id))
        return doc_type.doc_type_name if doc_type else "Unknown_Document"
    
    def _generate_unique_filename(self, type_name, original_filename, folder_path, used_names):
        """Generate a unique filename based on type name and handle duplicates"""
        # Clean the type name for use in filename
        clean_type_name = "".join(c for c in type_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        clean_type_name = clean_type_name.replace(' ', '_')
        
        # Get file extension
        file_ext = os.path.splitext(original_filename)[1]
        
        # Base filename
        base_filename = f"{clean_type_name}{file_ext}"
        
        # Check if filename already exists
        counter = 1
        final_filename = base_filename
        
        while final_filename in used_names or (folder_path / final_filename).exists():
            name_without_ext = os.path.splitext(base_filename)[0]
            final_filename = f"{name_without_ext}_{counter}{file_ext}"
            counter += 1
        
        used_names.add(final_filename)
        return final_filename

    def _cleanup_temp_files(self, file_paths):
        """Clean up temporary files if employee creation fails"""
        for file_path in file_paths:
            try:
                if isinstance(file_path, str):
                    file_path = Path(file_path)
                if file_path.exists():
                    file_path.unlink()
                    current_app.logger.info(f"Cleaned up temporary file: {file_path}")
            except Exception as e:
                current_app.logger.error(f"Failed to cleanup file {file_path}: {e}")

    def get_employee_skills_with_metadata(self, employee_id):
        if callable(self.db):
            session = self.db()  # It's a factory, create a session
        else:
            session = self.db  # It's already a session
        try:
            result = session.execute(
                text("""
                    SELECT s.skill_name, sc.category_name, es.skill_level, es.certified
                    FROM employee_skills es
                    JOIN skills s ON s.skill_id = es.skill_id
                    LEFT JOIN skill_categories sc ON s.category_id = sc.category_id
                    WHERE es.employee_id = :emp_id
                """),
                {"emp_id": employee_id}
            )

            return result.fetchall()
        finally:
            session.close()
   
    def _generate_business_id(self):
        """Generate sequential business ID in BIZYYYY-NNNN format"""
        session = self.db() if callable(self.db) else self.db
        try:
            # Get the current year
            current_year = datetime.now().year
            
            # Get the highest existing business ID for this year
            max_id = session.query(Employee.busness_id)\
                          .filter(Employee.busness_id.like(f'BIZ{current_year}-%'))\
                          .order_by(Employee.busness_id.desc())\
                          .first()
            
            if max_id and max_id[0]:
                # Extract the numeric part and increment
                last_num = int(max_id[0].split('-')[1])
                new_num = last_num + 1
            else:
                # First ID of the year
                new_num = 1
                
            # Format as BIZYYYY-000X
            return f'BIZ{current_year}-{str(new_num).zfill(4)}'
        except Exception as e:
            current_app.logger.error(f"Error generating business ID: {e}")
            # Fallback to UUID if sequential generation fails
            return f'BIZ{current_year}-{str(uuid.uuid4().int)[:4]}'
        finally:
            session.close()

    def business_id_exists(self, business_id):
        session = self.db() if callable(self.db) else self.db
        try:
            return session.query(Employee).filter(Employee.busness_id == business_id).first() is not None
        finally:
            if callable(self.db):
                session.close()
    
    def search_supervisors(self, query):
        """Search employees by name for supervisor selection"""
        session = self.db() if callable(self.db) else self.db
        try:
            return session.query(Employee).filter(
                Employee.is_active == True,
                (Employee.english_name.ilike(f'%{query}%') | 
                 Employee.arab_name.ilike(f'%{query}%') |
                 Employee.busness_id.ilike(f'%{query}%'))
            ).order_by(Employee.english_name).limit(10).all()
        finally:
            if callable(self.db):
                session.close()
     
    def search_employees(self, business_id=None, name=None, department=None, skill_name=None, skill_category=None, skill_level=None, certificate_type=None, document_type=None, supervisor_emp_id=None, position_id=None, hire_date_from=None, hire_date_to=None, sort_by=None):
        session = self.db() if callable(self.db) else self.db
        try:
            from sqlalchemy import or_, and_
            query = session.query(Employee).options(
                joinedload(Employee.department),
                joinedload(Employee.skills),
                joinedload(Employee.documents)
            )
            if business_id:
                query = query.filter(Employee.busness_id.ilike(f"%{business_id}%"))
            if name:
                query = query.filter(or_(Employee.english_name.ilike(f"%{name}%"), Employee.arab_name.ilike(f"%{name}%")))
            if department:
                query = query.join(Employee.department).filter(Employee.department.has(department_name=department))
            if supervisor_emp_id:
                query = query.filter(Employee.supervisor_emp_id == supervisor_emp_id)
            if position_id:
                query = query.filter(Employee.position_id == int(position_id))
            if hire_date_from:
                from datetime import datetime
                try:
                    date_from = datetime.strptime(hire_date_from, '%Y-%m-%d').date()
                    query = query.filter(Employee.hire_date >= date_from)
                except Exception:
                    pass
            if hire_date_to:
                from datetime import datetime
                try:
                    date_to = datetime.strptime(hire_date_to, '%Y-%m-%d').date()
                    query = query.filter(Employee.hire_date <= date_to)
                except Exception:
                    pass
            # Skill filters
            if skill_name:
                query = query.join(Employee.skills).filter(Skill.skill_name.ilike(f"%{skill_name}%"))
            if skill_category:
                query = query.join(Employee.skills).filter(Skill.category_id == skill_category)
            if skill_level:
                query = query.join(Employee.skills).filter(employee_skills.c.skill_level == skill_level)
            # Certificate/document filters
            if certificate_type:
                query = query.join(Employee.documents).filter(Employee.documents.any(cert_type_id=certificate_type))
            if document_type:
                query = query.join(Employee.documents).filter(Employee.documents.any(doc_type_id=document_type))
            # Sorting
            if sort_by == 'name_asc':
                query = query.order_by(Employee.english_name.asc())
            elif sort_by == 'name_desc':
                query = query.order_by(Employee.english_name.desc())
            elif sort_by == 'id_asc':
                query = query.order_by(Employee.busness_id.asc())
            elif sort_by == 'id_desc':
                query = query.order_by(Employee.busness_id.desc())
            elif sort_by == 'hiredate_asc':
                query = query.order_by(Employee.hire_date.asc())
            elif sort_by == 'hiredate_desc':
                query = query.order_by(Employee.hire_date.desc())

            employees = query.distinct().all()

            result = []
            for emp in employees:
                result.append({
                    'id': emp.emp_id,
                    'business_id': emp.busness_id,
                    'name': f"{emp.english_name} ({emp.arab_name})",
                    'department': emp.department.department_name if emp.department else '',
                    'skills': {
                        'Technical': [s.skill_name for s in emp.skills],
                    }
                })
            return result
        finally:
            if callable(self.db):
                session.close()
     