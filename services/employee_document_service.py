from werkzeug.utils import secure_filename
import os
import uuid
from pathlib import Path
from datetime import datetime
from database.connection import db
from database.repositories.certificate_type_repository import CertificateTypeRepository
from database.repositories.document_type_repository import DocumentTypeRepository
from database.repositories.employee_document_repository import EmployeeDocumentRepository

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
            
            # Process general documents
            if files and any(f for f in files.getlist('document_file[]') if f.filename):
                self._save_general_documents(employee_id, form_data, files, upload_path)
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            raise RuntimeError(f"Document processing error: {str(e)}")

    def _save_certificates(self, employee_id, form_data, files, upload_path):
        """Handle certificate file uploads"""
        for idx, (file, cert_type_id, org, months) in enumerate(zip(
            [f for f in files.values() if f.filename and 'document_file_' in f.name],
            form_data.getlist('certificate_type_id[]'),
            form_data.getlist('issuing_organization[]'),
            form_data.getlist('validity_period_months[]')
        )):
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
        for idx, (file, doc_type_id) in enumerate(zip(
            files.getlist('document_file[]'),
            form_data.getlist('general_document_type_id[]')
        )):
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
        """Get a document by its ID"""
        session = self.db() if callable(self.db) else self.db
        try:
            from models.employee_document import EmployeeDocument
            document = session.query(EmployeeDocument).filter_by(document_id=document_id).first()
            return document
        finally:
            if callable(self.db):
                session.close()