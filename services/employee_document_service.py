from werkzeug.utils import secure_filename
import os
import uuid
from pathlib import Path
from datetime import datetime
from database.connection import db
from database.repositories.certificate_type_repository import CertificateTypeRepository
from database.repositories.document_type_repository import DocumentTypeRepository
from database.repositories.employee_document_repository import EmployeeDocumentRepository
from models.employee_document import EmployeeDocument

class EmployeeDocumentService:
    def __init__(self, db_session=None):
        self.db = db_session if db_session is not None else db()
        self.certificate_repo = CertificateTypeRepository()
        self.document_type_repo = DocumentTypeRepository()
        self.document_repo = EmployeeDocumentRepository()
        self.upload_folder = 'employee_uploads'  # Default folder name

    def _get_upload_path(self):
        """Get the upload path, creating it if needed"""
        upload_path = Path(self.upload_folder)
        upload_path.mkdir(parents=True, exist_ok=True)
        return upload_path

    def save_employee_documents(self, employee_id, form_data, files):
        """Handle all document processing"""
        try:
            upload_path = self._get_upload_path()
            
            # Process certificates if they exist
            if 'certified[]' in form_data:
                self._save_certificates(employee_id, form_data, files, upload_path)
            
            # Process general documents (support dict-like in tests)
            def _files_getlist(files_map, key):
                if hasattr(files_map, 'getlist'):
                    return files_map.getlist(key)
                val = files_map.get(key)
                if val is None:
                    return []
                return val if isinstance(val, list) else [val]

            if files:
                general_files = _files_getlist(files, 'document_file[]')
                if not general_files and hasattr(files, 'getlist'):
                    general_files = files.getlist('document_files[]')
                elif not general_files and isinstance(files, dict) and 'document_files[]' in files:
                    val = files['document_files[]']
                    general_files = val if isinstance(val, list) else [val]
                if any(getattr(f, 'filename', '') for f in general_files):
                    # Rewrap as a simple dict with getlist interface for downstream calls
                    class _Wrap:
                        def __init__(self, arr):
                            self._arr = arr
                        def getlist(self, _):
                            return self._arr
                    self._save_general_documents(employee_id, form_data, _Wrap(general_files), upload_path)
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            raise RuntimeError(f"Document processing error: {str(e)}")

    def _save_certificates(self, employee_id, form_data, files, upload_path):
        """Handle certificate file uploads"""
        file_candidates = []
        if hasattr(files, 'keys'):
            for k in files.keys():
                if k.startswith('document_file_') or k == 'certificate_file[]':
                    val = files.get(k)
                    if val:
                        file_candidates.append(val)
        else:
            for k, v in (files.items() if hasattr(files, 'items') else []):
                if str(k).startswith('document_file_') or k == 'certificate_file[]':
                    file_candidates.append(v)

        cert_types = form_data.getlist('certificate_type_id[]') if hasattr(form_data, 'getlist') else [form_data.get('certificate_type_id[]')] if form_data.get('certificate_type_id[]') else []
        orgs = form_data.getlist('issuing_organization[]') if hasattr(form_data, 'getlist') else [form_data.get('issuing_organization[]')] if form_data.get('issuing_organization[]') else []
        months_list = form_data.getlist('validity_period_months[]') if hasattr(form_data, 'getlist') else [form_data.get('validity_period_months[]')] if form_data.get('validity_period_months[]') else []

        for idx, (file, cert_type_id, org, months) in enumerate(zip(file_candidates, cert_types, orgs, months_list)):
            try:
                filename = f"cert_{employee_id}_{uuid.uuid4().hex}{os.path.splitext(file.filename)[1]}"
                file_path = upload_path / filename
                file.save(file_path)
                
                self.document_repo.save_certificate(
                    employee_id=employee_id,
                    cert_type_id=int(cert_type_id),
                    issuing_organization=org,
                    validity_period=int(months) if months else None,
                    upload_date=datetime.now(),
                    file_path=str(file_path)
                )
            except Exception as e:
                raise RuntimeError(f"Certificate {idx} failed: {str(e)}")

    def _save_general_documents(self, employee_id, form_data, files, upload_path):
        """Handle general document uploads"""
        file_list = files.getlist('document_file[]') if hasattr(files, 'getlist') else files
        type_list = form_data.getlist('general_document_type_id[]') if hasattr(form_data, 'getlist') else form_data.get('general_document_type_id[]', [])
        if not isinstance(type_list, list):
            type_list = [type_list]
        for idx, (file, doc_type_id) in enumerate(zip(file_list, type_list)):
            if not file.filename:
                continue
                
            try:
                filename = f"doc_{employee_id}_{uuid.uuid4().hex}{os.path.splitext(file.filename)[1]}"
                file_path = upload_path / filename
                file.save(file_path)
                
                self.document_repo.save_document(
                    employee_id=employee_id,
                    doc_type_id=int(doc_type_id),
                    file_path=str(file_path),
                    upload_date=datetime.now()
                )
            except Exception as e:
                raise RuntimeError(f"Document {idx} failed: {str(e)}")

    # Keep all other existing methods exactly the same
    def get_all_certificate_types(self):
        return self.certificate_repo.get_all_certificate_types()

    def get_all_document_types(self):
        return self.document_type_repo.get_all_document_types()

    def get_employee_documents(self, employee_id):
        return self.document_repo.get_by_employee(employee_id)

    def delete_document(self, document_id):
        return self.document_repo.delete(document_id)
  
    def get_document(self, document_id):
        """Fetch a single document by its ID"""
        return self.document_repo.get_by_id(document_id)

