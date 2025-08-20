
import os
import uuid
from pathlib import Path
from werkzeug.utils import secure_filename
from models.employee_document import EmployeeDocument
from flask import current_app, request
from datetime import datetime

from services.document_validator import DocumentValidator

def handle_file_uploads(session, employee_id, files, form_data=None):
    """
    Handles file uploads from a form, saves them, and creates
    corresponding database entries.

    Args:
        session: The SQLAlchemy database session.
        employee_id: The ID of the employee to link the documents to.
        files: The request.files object containing the uploaded files.
        form_data: The form data containing document type IDs.
    """
    temp_files = []
    try:
        # Debug logging
        current_app.logger.info(f"File upload handler called for employee {employee_id}")
        current_app.logger.info(f"Files keys: {list(files.keys())}")
        current_app.logger.info(f"Form data keys: {list(form_data.keys()) if form_data else 'None'}")
        
        # Helper to support dict-like inputs in tests and Werkzeug FileStorage
        class _SimpleFile:
            def __init__(self, stream, filename):
                self._stream = stream
                self.filename = filename
            def save(self, path):
                with open(path, 'wb') as f:
                    if hasattr(self._stream, 'read'):
                        f.write(self._stream.read())
                    else:
                        f.write(self._stream)

        def _files_getlist(files_map, key):
            if hasattr(files_map, 'getlist'):
                return files_map.getlist(key)
            val = files_map.get(key)
            if val is None:
                return []
            if isinstance(val, list):
                result = []
                for item in val:
                    if isinstance(item, tuple) and len(item) == 2:
                        result.append(_SimpleFile(item[0], item[1]))
                    else:
                        result.append(item)
                return result
            if isinstance(val, tuple) and len(val) == 2:
                return [_SimpleFile(val[0], val[1])]
            return [val]

        # Handle general documents (support both singular and plural forms)
        document_key = None
        if 'general_document_files[]' in files:
            document_key = 'general_document_files[]'
        elif 'general_document_file[]' in files:
            document_key = 'general_document_file[]'
        
        if document_key:
            general_documents = _files_getlist(files, document_key)
            if hasattr(form_data, 'getlist'):
                doc_type_ids = form_data.getlist('general_document_type_id[]') if form_data else []
                file_names = form_data.getlist('general_document_file_names[]') if form_data else []
            else:
                raw_types = form_data.get('general_document_type_id[]', []) if form_data else []
                doc_type_ids = raw_types if isinstance(raw_types, list) else [raw_types]
                raw_names = form_data.get('general_document_file_names[]', []) if form_data else []
                file_names = raw_names if isinstance(raw_names, list) else [raw_names]
            
            current_app.logger.info(f"Found {len(general_documents)} general documents using key: {document_key}")
            current_app.logger.info(f"Found {len(doc_type_ids)} document type IDs")
            current_app.logger.info(f"Found {len(file_names)} file names")
            
            # If we have file names but no actual files, we need to handle this differently
            if not general_documents and file_names:
                current_app.logger.warning("Have file names but no actual files - this might be from edit form")
                return
                
            if not general_documents:
                current_app.logger.warning("No general document files found")
                return

            for i, doc_file in enumerate(general_documents):
                if doc_file.filename == '':
                    continue
                    
                doc_type_id = doc_type_ids[i] if i < len(doc_type_ids) else None

                # Validate general document data
                doc_data = {
                    'doc_type_id': doc_type_id,
                    'document_name': secure_filename(doc_file.filename),
                    'file_path': None  # Will be set after file save
                }
                
                is_valid, error_msg = DocumentValidator.validate_document_data(doc_data)
                if not is_valid:
                    current_app.logger.warning(f"Skipping invalid general document: {error_msg}")
                    continue

                if doc_type_id:
                    try:
                        doc_type_id_int = int(doc_type_id)
                    except Exception:
                        current_app.logger.warning(f"Invalid document type id '{doc_type_id}' for file {doc_file.filename}; saving without type.")
                        doc_type_id_int = None
                else:
                    doc_type_id_int = None

                # proceed even if type is missing
                if True: # This 'if True' can be removed if the validation above is sufficient
                    # Get employee business ID to create proper folder structure
                    from models.employee import Employee
                    employee = session.query(Employee).filter_by(emp_id=employee_id).first()
                    if not employee:
                        current_app.logger.error(f"Employee {employee_id} not found")
                        continue
                    
                    # Create employee-specific folder structure
                    employee_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], employee.busness_id)
                    documents_folder = os.path.join(employee_folder, 'documents')
                    
                    # Ensure employee-specific directories exist
                    os.makedirs(documents_folder, exist_ok=True)
                    
                    # Secure the filename to prevent directory traversal attacks
                    filename = secure_filename(doc_file.filename)
                    # Create a unique filename to avoid conflicts
                    unique_filename = f"{uuid.uuid4()}_{filename}"
                    upload_path = os.path.join(documents_folder, unique_filename)
                    
                    # Save the file
                    doc_file.save(upload_path)
                    temp_files.append(upload_path)

                    # Create a new EmployeeDocument object and add it to the session
                    new_document = EmployeeDocument(
                        employee_id=employee_id,
                        doc_type_id=doc_type_id_int,
                        file_path=upload_path,
                        document_name=filename,
                        upload_date=datetime.now().date()
                    )
                    session.add(new_document)
                    session.flush()
                    current_app.logger.info(f"Saved new document id={new_document.document_id} for employee {employee_id} ({employee.busness_id}): {unique_filename}, type_id={doc_type_id_int}")
                    

            # Also support certificate-like uploads used in tests and edit page
            if hasattr(files, 'keys'):
                cert_keys = [k for k in files.keys() if k.startswith('document_file_') or k == 'certificate_file[]']
            else:
                cert_keys = [k for k in files if str(k).startswith('document_file_') or k == 'certificate_file[]']

            # Gather certificate metadata arrays, if present
            cert_type_ids = form_data.getlist('certificate_type_id[]') if hasattr(form_data, 'getlist') else [form_data.get('certificate_type_id[]')] if form_data and form_data.get('certificate_type_id[]') else []
            orgs = form_data.getlist('issuing_organization[]') if hasattr(form_data, 'getlist') else [form_data.get('issuing_organization[]')] if form_data and form_data.get('issuing_organization[]') else []
            validity_months = form_data.getlist('validity_period_months[]') if hasattr(form_data, 'getlist') else [form_data.get('validity_period_months[]')] if form_data and form_data.get('validity_period_months[]') else []

            cert_files = []
            for key in cert_keys:
                cert_files.extend(_files_getlist(files, key))

            for idx, cert_file in enumerate(cert_files):
                if not cert_file or not getattr(cert_file, 'filename', ''):
                    continue
                
                # Prepare document data for validation
                doc_data = {
                    'cert_type_id': cert_type_ids[idx] if idx < len(cert_type_ids) else None,
                    'document_name': secure_filename(cert_file.filename),
                    'skill_name': None,  # You can extract this from form_data if needed
                    'issuing_organization': orgs[idx] if idx < len(orgs) else None,
                    'validity_period_months': validity_months[idx] if idx < len(validity_months) else None
                }
                
                # Validate before creating
                is_valid, error_msg = DocumentValidator.validate_document_data(doc_data)
                if not is_valid:
                    current_app.logger.warning(f"Skipping invalid certificate: {error_msg}")
                    continue
                
                # File saving logic
                from models.employee import Employee
                employee = session.query(Employee).filter_by(emp_id=employee_id).first()
                if not employee:
                    continue
                employee_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], employee.busness_id)
                certificates_folder = os.path.join(employee_folder, 'certificates')
                os.makedirs(certificates_folder, exist_ok=True)
                filename = secure_filename(cert_file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                upload_path = os.path.join(certificates_folder, unique_filename)
                cert_file.save(upload_path)
                temp_files.append(upload_path)

                # Convert validity period to integer if provided
                months_int = None
                if doc_data['validity_period_months'] and str(doc_data['validity_period_months']).isdigit():
                    months_int = int(doc_data['validity_period_months'])

                # Create the document (VALIDATED)
                new_document = EmployeeDocument(
                    employee_id=employee_id,
                    cert_type_id=int(doc_data['cert_type_id']),  # Validator ensures this is valid
                    file_path=upload_path,
                    document_name=doc_data['document_name'],
                    upload_date=datetime.now().date(),
                    issuing_organization=doc_data['issuing_organization'],
                    validity_period_months=months_int
                )
                session.add(new_document)
                session.flush()
                current_app.logger.info(f"Saved certificate document id={new_document.document_id} for employee {employee_id} ({employee.busness_id}): {unique_filename}, cert_type_id={doc_data['cert_type_id']}")

    except Exception as e:
        current_app.logger.error(f"File upload failed: {e}")
        # Clean up any temporary files that were already saved
        for f in temp_files:
            if os.path.exists(f):
                os.remove(f)
        raise RuntimeError(f"Could not process file uploads: {e}")
