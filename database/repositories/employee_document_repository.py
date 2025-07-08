from datetime import datetime
from models.employee_document import EmployeeDocument
from database.connection import db  # db is SessionLocal

class EmployeeDocumentRepository:
    def save_certificate(self, employee_id, cert_type_id, issuing_organization, validity_period, upload_date, file_path=None):
        session = db()
        try:
            document = EmployeeDocument(
                employee_id=employee_id,
                certificate_type_id=cert_type_id,
                skill_name=None,
                document_type_id=None,
                file_path=file_path,
                uploaded_at=upload_date,
                issuing_organization=issuing_organization,
                validity_period_months=validity_period
            )
            session.add(document)
            session.commit()
            return document
        finally:
            session.close()

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