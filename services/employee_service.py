import uuid
import json
import os
from pathlib import Path
from flask import current_app
from datetime import datetime
from werkzeug.utils import secure_filename
from sqlalchemy import text, select
from sqlalchemy.orm import joinedload
from database.repositories.employee_repository import EmployeeRepository
from database.repositories.position_repository import PositionRepository
from database.repositories.skill_repository import SkillRepository
from database.connection import db
from models.employee import Employee
from models.skill import Skill
from models.skill_category import SkillCategory
from models.employee_document import EmployeeDocument
from models.certificate_type import CertificateType
from models.document_type import DocumentType
from models.associations import employee_skills
from processor.employee_processor import EmployeeDocumentProcessor

class EmployeeService:
    def __init__(self, db_session=None):
        self.db = db_session if db_session is not None else db
        self.repository = EmployeeRepository()


    def _process_json_skills(self, employee_id: int, business_id: str, session):
        """Process skills from JSON file (now uses converted/json_files)"""
        json_path = Path("converted/json_files") / f"{business_id}.json"
        if not json_path.exists():
            current_app.logger.debug(f"No JSON file found at {json_path}")
            return
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            for skill_data in data.get('skills', []):
                skill_name = skill_data.get('skill', '').strip()
                if not skill_name:
                    continue
                    
                # Get or create category
                category_name = skill_data.get('category', '').strip()
                category = None
                if category_name:
                    category = session.execute(
                        select(SkillCategory)
                        .where(SkillCategory.category_name.ilike(category_name))
                    ).scalar_one_or_none()
                    if not category:
                        category = SkillCategory(category_name=category_name)
                        session.add(category)
                        session.flush()
                
                # Get or create skill
                skill = session.execute(
                    select(Skill).where(Skill.skill_name.ilike(skill_name))
                ).scalar_one_or_none()
                if not skill:
                    skill = Skill(
                        skill_name=skill_name,
                        category_id=category.category_id if category else None
                    )
                    session.add(skill)
                    session.flush()
                
                # Create association if not exists
                if not session.execute(
                    select(employee_skills)
                    .where(
                        (employee_skills.c.employee_id == employee_id) &
                        (employee_skills.c.skill_id == skill.skill_id)
                    )
                ).scalar_one_or_none():
                    session.execute(
                        employee_skills.insert().values(
                            employee_id=employee_id,
                            skill_id=skill.skill_id,
                            skill_level=skill_data.get('level'),
                            certified=skill_data.get('certified', False)
                        )
                    )
            
            # Archive the file after processing
            processed_dir = Path("converted/json_processed")
            processed_dir.mkdir(exist_ok=True)
            json_path.rename(processed_dir / f"{business_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json")
            
        except json.JSONDecodeError as e:
            current_app.logger.error(f"Invalid JSON in {json_path}: {str(e)}")
        except Exception as e:
            current_app.logger.error(f"Failed to process JSON skills: {str(e)}")
            raise

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
                'is_active': is_active,
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
            existing_employee = session.query(Employee).filter_by(email=form_data.get('email')).first()
            if existing_employee:
                raise RuntimeError(f"An employee with email {form_data.get('email')} already exists.")

            business_id = form_data.get('business_id') or self._generate_business_id()

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

            processor = EmployeeDocumentProcessor(employee.emp_id, employee.busness_id)
            processor.process_documents()

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

    def _process_employee_skills(self, form_data, employee_id: int, session=None) -> None:
        if session is None:
            session = self.db() if callable(self.db) else self.db
            should_close = True
        else:
            should_close = False

        try:
            certified_indices = form_data.getlist('certified[]')
            
            session.execute(
                employee_skills.delete().where(employee_skills.c.employee_id == employee_id)
            )

            skill_names = form_data.getlist('skill_name[]')
            skill_categories = form_data.getlist('skill_category[]')
            skill_levels = form_data.getlist('skill_level[]')

            for idx, (name, category, level) in enumerate(zip(skill_names, skill_categories, skill_levels)):
                name = name.strip()
                if not name:
                    continue

                is_certified = name in certified_indices
                skill = session.query(Skill).filter_by(skill_name=name).first()
                if not skill:
                    skill = Skill(
                        skill_name=name,
                        category_id=int(category) if category and category != "select category" else None
                    )
                    session.add(skill)
                    session.flush()
                
                session.execute(employee_skills.insert().values(
                    employee_id=employee_id,
                    skill_id=skill.skill_id,
                    skill_level=level if level and level != "select level" else None,
                    certified=1 if is_certified else 0
                ))

            employee = session.query(Employee).get(employee_id)
            if employee:
                self._process_json_skills(employee_id, employee.busness_id, session)

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

    def _prepare_skills_data(self, form_data):
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
        try:
            employee = self.repository.get_employee(employee_id)
            if not employee:
                raise ValueError("Employee not found")
            return employee
        except Exception as e:
            current_app.logger.error(f"Error getting employee: {e}")
            raise

    def delete_employee(self, employee_id: int) -> bool:
        session = self.db() if callable(self.db) else self.db
        should_close = callable(self.db)
        
        try:
            employee = session.query(Employee).options(
                joinedload(Employee.documents),
                joinedload(Employee.skills)
            ).filter_by(emp_id=employee_id).first()
            
            if not employee:
                return False
            
            business_id = employee.busness_id
            
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
            
            employee.skills.clear()
            
            session.delete(employee)
            session.commit()
            
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
        temp_files = []

        try:
            employee = session.query(Employee).get(employee_id)
            if not employee:
                return False

            new_email = form_data.get('email')
            if new_email:
                existing_employee = session.query(Employee).filter(
                    Employee.email == new_email,
                    Employee.emp_id != employee_id
                ).first()
                if existing_employee:
                    raise RuntimeError(f"An employee with email {new_email} already exists.")

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

            self._process_employee_skills(form_data, employee_id, session)

            if files:
                current_app.logger.info(f"Processing new documents for employee {employee_id}")
                temp_files = self._process_employee_documents(form_data, files, employee_id, employee.busness_id, session)

            session.commit()

            processor = EmployeeDocumentProcessor(employee_id, employee.busness_id)
            processor.process_documents()

            return True

        except Exception as e:
            session.rollback()
            if temp_files:
                self._cleanup_temp_files(temp_files)
            current_app.logger.error(f"Employee update failed: {e}")
            raise RuntimeError(f"Could not update employee: {e}")

        finally:
            if callable(self.db):
                session.close()
   
    def _process_employee_documents(self, form_data, files, employee_id: int, business_id: str, session=None) -> list:
        if session is None:
            session = self.db() if callable(self.db) else self.db
            should_close = True
        else:
            should_close = False
            
        saved_files = []
        
        try:
            base_path = Path('employee_documents')
            employee_folder = base_path / business_id
            certificates_folder = employee_folder / 'certificates'
            documents_folder = employee_folder / 'documents'
            
            certificates_folder.mkdir(parents=True, exist_ok=True)
            documents_folder.mkdir(parents=True, exist_ok=True)
            
            # FIX: Define certified_indices before use
            certified_indices = form_data.getlist('certified[]') if hasattr(form_data, 'getlist') else []
            used_certificate_names = set()
            used_document_names = set()
            
            certificate_files = {}
            for key in files.keys():
                if key.startswith('document_file_') and key.endswith('[]'):
                    try:
                        file_index = int(key.replace('document_file_', '').replace('[]', ''))
                        certificate_files[file_index] = files[key]
                    except ValueError:
                        continue
            
            skill_names = form_data.getlist('skill_name[]') if hasattr(form_data, 'getlist') else []
            for idx, is_certified in enumerate(certified_indices):
                if is_certified:
                    file = certificate_files.get(idx)
                    if not file:
                        continue
                    
                    if file and file.filename:
                        cert_type_id = form_data.getlist('certificate_type_id[]')[idx] if hasattr(form_data, 'getlist') else form_data.get('certificate_type_id[]')
                        cert_type = session.query(CertificateType).get(int(cert_type_id)) if cert_type_id else None
                        cert_type_name = self._get_certificate_type_name(session, cert_type_id)
                        
                        filename = self._generate_unique_filename(
                            cert_type_name, 
                            file.filename, 
                            certificates_folder, 
                            used_certificate_names
                        )
                        
                        file_path = certificates_folder / filename
                        file.save(file_path)
                        saved_files.append(file_path)
                        
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
                            doc_type_id=None,
                            document_name=filename,
                            file_path=str(file_path),
                            upload_date=datetime.utcnow().date(),
                            skill_name=skill_names[idx] if idx < len(skill_names) else None,
                            issuing_organization=issuing_org,
                            validity_period_months=validity_months
                        )
                        session.add(document)
            
            general_files = files.getlist('general_document_file[]') if hasattr(files, 'getlist') else []
            doc_type_ids = form_data.getlist('general_document_type_id[]') if hasattr(form_data, 'getlist') else []
            
            for file, doc_type_id in zip(general_files, doc_type_ids):
                if file and file.filename:
                    doc_type_name = self._get_document_type_name(session, doc_type_id)
                    
                    filename = self._generate_unique_filename(
                        doc_type_name, 
                        file.filename, 
                        documents_folder, 
                        used_document_names
                    )
                    
                    file_path = documents_folder / filename
                    file.save(file_path)
                    saved_files.append(file_path)
                    
                    document = EmployeeDocument(
                        employee_id=employee_id,
                        doc_type_id=int(doc_type_id) if doc_type_id else None,
                        cert_type_id=None,
                        document_name=filename,
                        file_path=str(file_path),
                        upload_date=datetime.utcnow().date()
                    )
                    session.add(document)
                    
        except Exception as e:
            if should_close:
                session.rollback()
            if saved_files:
                self._cleanup_temp_files(saved_files)
            raise RuntimeError(f"Document processing failed: {str(e)}")
        finally:
            if should_close and callable(self.db):
                session.close()
        
        return saved_files

    def _get_certificate_type_name(self, session, cert_type_id):
        if not cert_type_id:
            return "Unknown_Certificate"
        
        cert_type = session.query(CertificateType).get(int(cert_type_id))
        return cert_type.type_name if cert_type else "Unknown_Certificate"
    
    def _get_document_type_name(self, session, doc_type_id):
        if not doc_type_id:
            return "Unknown_Document"
        
        doc_type = session.query(DocumentType).get(int(doc_type_id))
        return doc_type.doc_type_name if doc_type else "Unknown_Document"
    
    def _generate_unique_filename(self, type_name, original_filename, folder_path, used_names):
        clean_type_name = "".join(c for c in type_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        clean_type_name = clean_type_name.replace(' ', '_')
        
        file_ext = os.path.splitext(original_filename)[1]
        base_filename = f"{clean_type_name}{file_ext}"
        counter = 1
        final_filename = base_filename
        
        while final_filename in used_names or (folder_path / final_filename).exists():
            name_without_ext = os.path.splitext(base_filename)[0]
            final_filename = f"{name_without_ext}_{counter}{file_ext}"
            counter += 1
        
        used_names.add(final_filename)
        return final_filename

    def _cleanup_temp_files(self, file_paths):
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
            session = self.db()
        else:
            session = self.db
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
        session = self.db() if callable(self.db) else self.db
        try:
            current_year = datetime.now().year
            
            max_id = session.query(Employee.busness_id)\
                          .filter(Employee.busness_id.like(f'BIZ{current_year}-%'))\
                          .order_by(Employee.busness_id.desc())\
                          .first()
            
            if max_id and max_id[0]:
                last_num = int(max_id[0].split('-')[1])
                new_num = last_num + 1
            else:
                new_num = 1
                
            return f'BIZ{current_year}-{str(new_num).zfill(4)}'
        except Exception as e:
            current_app.logger.error(f"Error generating business ID: {e}")
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
            if skill_name:
                query = query.join(Employee.skills).filter(Skill.skill_name.ilike(f"%{skill_name}%"))
            if skill_category:
                query = query.join(Employee.skills).filter(Skill.category_id == skill_category)
            if skill_level:
                query = query.join(Employee.skills).filter(employee_skills.c.skill_level == skill_level)
            if certificate_type:
                query = query.join(Employee.documents).filter(Employee.documents.any(cert_type_id=certificate_type))
            if document_type:
                query = query.join(Employee.documents).filter(Employee.documents.any(doc_type_id=document_type))
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
                    'emp_id': emp.emp_id,
                    'business_id': emp.busness_id,
                    'name': f"{emp.english_name} ({emp.arab_name})",
                    'department': emp.department.department_name if emp.department else '',
                    'supervisor_emp_id': emp.supervisor_emp_id,
                    'skills': {
                        'Technical': [s.skill_name for s in emp.skills],
                    }
                })
            return result
        finally:
            if callable(self.db):
                session.close()