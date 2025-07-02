from database.repositories.certificate_type_repository import CertificateTypeRepository
from database.repositories.document_type_repository import DocumentTypeRepository
from database.repositories.employee_document_repository import EmployeeDocumentRepository

class EmployeeDocumentService:
    def __init__(self):
        self.certificate_repo = CertificateTypeRepository()
        self.document_type_repo = DocumentTypeRepository()
        self.document_repo = EmployeeDocumentRepository()

    def get_all_certificate_types(self):
        return self.certificate_repo.get_all_certificate_types()

    def get_all_document_types(self):
        return self.document_type_repo.get_all_document_types()

    def save_employee_documents(self, employee_id, form_data, files):
        skill_names = form_data.getlist('skill_name[]')
        cert_type_ids = form_data.getlist('certificate_type_id[]')
        doc_type_ids = form_data.getlist('document_type_id[]')
        uploaded_files = files.getlist('document_file[]')

        for i in range(len(skill_names)):
            file = uploaded_files[i]
            filename = file.filename
            if not filename:
                continue  # skip empty uploads

            # Save file to disk
            from werkzeug.utils import secure_filename
            import os
            from flask import current_app

            safe_name = secure_filename(filename)
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], safe_name)
            file.save(upload_path)

            # Save record to DB
            self.document_repo.save_document(
                employee_id=employee_id,
                skill_name=skill_names[i],
                cert_type_id=cert_type_ids[i],
                doc_type_id=doc_type_ids[i],
                file_path=upload_path
            )