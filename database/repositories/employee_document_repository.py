from datetime import datetime
import os

from flask import current_app
from models.employee_document import EmployeeDocument
from database.connection import db  # db is SessionLocal
from werkzeug.utils import secure_filename

class EmployeeDocumentRepository:
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
            certificate_type_ids,
            issuing_orgs,
            validity_months
        ):
            # 🛡️ Defensive check for empty file
            if not file or not file.filename.strip():
                print("⚠️ Skipping empty certificate file input")
                continue
            print(f"📎 Certificate file received: {file.filename} | Content-Type: {file.content_type}")

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

    def save_document(self, employee_id, skill_name, cert_type_id, doc_type_id, file_path):
        session = db()
        try:
            document = EmployeeDocument(
                employee_id=employee_id,
                skill_name=skill_name,
                certificate_type_id=cert_type_id,
                document_type_id=doc_type_id,
                file_path=file_path,
                uploaded_at=datetime.utcnow()
            )
            session.add(document)
            session.commit()
            return document
        finally:
            session.close()
    
    def delete(self, document_id):
        """Delete a document by its ID"""
        session = db()
        try:
            document = session.query(EmployeeDocument).filter_by(document_id=document_id).first()
            if document:
                # Delete the physical file if it exists
                if document.file_path and os.path.exists(document.file_path):
                    os.remove(document.file_path)
                
                session.delete(document)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            current_app.logger.error(f"Error deleting document {document_id}: {e}")
            return False
        finally:
            session.close()
    
    def get_by_employee(self, employee_id):
        """Get all documents for an employee"""
        session = db()
        try:
            documents = session.query(EmployeeDocument).filter_by(employee_id=employee_id).all()
            return documents
        finally:
            session.close()