from database.connection import db
from models.employee_document import EmployeeDocument
from datetime import datetime

class EmployeeDocumentRepository:
    def save_document(self, employee_id, skill_name, cert_type_id, doc_type_id, file_path):
        document = EmployeeDocument(
            employee_id=employee_id,
            skill_name=skill_name,
            certificate_type_id=cert_type_id,
            document_type_id=doc_type_id,
            file_path=file_path,
            uploaded_at=datetime.utcnow()
        )
        db.add(document)
        db.commit()
        return document