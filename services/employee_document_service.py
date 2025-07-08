from werkzeug.utils import secure_filename
import os
from flask import current_app
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

    def get_all_certificate_types(self):
        return self.certificate_repo.get_all_certificate_types()

    def get_all_document_types(self):
        return self.document_type_repo.get_all_document_types()

    def save_employee_documents(self, employee_id, form_data, files):
        """Handle saving all types of employee documents and certificates"""
        try:
            # Process certificates if certified checkbox is checked
            if 'certified[]' in form_data:
                self._save_certificates(employee_id, form_data, files)
            # Process general documents
            if files and any(files.getlist('document_file[]')):
                self._save_general_documents(employee_id, form_data, files)

            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            current_app.logger.error(f"Error saving documents: {str(e)}")
            raise RuntimeError(f"Failed to save documents: {str(e)}")

    def _save_certificates(self, employee_id, form_data, files):
        certificate_files = [
        file for key, file in files.items(multi=True)
        if key.startswith('document_file_')
        ]
        certificate_type_ids = form_data.getlist('certificate_type_id[]')
        issuing_orgs = form_data.getlist('issuing_organization[]')
        validity_months = form_data.getlist('validity_period_months[]')

        for file, cert_type_id, org, months in zip(
        certificate_files,
        form_data.getlist('certificate_type_id[]'),
        form_data.getlist('issuing_organization[]'),
        form_data.getlist('validity_period_months[]')
    ):
            if not file or not file.filename:
                continue

            filename = secure_filename(file.filename)
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(upload_path)

            self.document_repo.save_certificate(
                employee_id=employee_id,
                cert_type_id=int(cert_type_id),
                issuing_organization=org,
                validity_period=int(months) if months else None,
                upload_date=datetime.utcnow(),
                file_path=upload_path
            )
    def _save_general_documents(self, employee_id, form_data, files):
        """Handle file uploads and document saving"""
        for file, doc_type_id in zip(
            files.getlist('document_file[]'),
            form_data.getlist('general_document_type_id[]')
        ):
            if not file.filename:
                continue

            # Secure and save the file
            filename = secure_filename(file.filename)
            upload_path = os.path.join(
                current_app.config['UPLOAD_FOLDER'], 
                filename
            )
            file.save(upload_path)

            # Create document record
            doc_data = {
                'employee_id': employee_id,
                'doc_type_id': int(doc_type_id),
                'file_path': upload_path,
                'upload_date': datetime.utcnow()
            }
            self.document_repo.save_document(**doc_data)

    def get_employee_documents(self, employee_id):
        """Retrieve all documents for an employee"""
        return self.document_repo.get_by_employee(employee_id)

    def delete_document(self, document_id):
        """Delete a specific document"""
        return self.document_repo.delete(document_id)