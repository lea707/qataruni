#
# This file provides a utility function for handling file uploads
# to ensure consistency across the application.
#

import os
import uuid
from pathlib import Path
from werkzeug.utils import secure_filename
from models.employee_document import EmployeeDocument
from flask import current_app, request
from datetime import datetime

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
        
        # Handle general documents (support both singular and plural forms)
        document_key = None
        if 'general_document_files[]' in files:
            document_key = 'general_document_files[]'
        elif 'general_document_file[]' in files:
            document_key = 'general_document_file[]'
        
        if document_key:
            general_documents = files.getlist(document_key)
            doc_type_ids = form_data.getlist('general_document_type_id[]') if form_data else []
            file_names = form_data.getlist('general_document_file_names[]') if form_data else []
            
            current_app.logger.info(f"Found {len(general_documents)} general documents using key: {document_key}")
            current_app.logger.info(f"Found {len(doc_type_ids)} document type IDs")
            current_app.logger.info(f"Found {len(file_names)} file names")
            
            # If we have file names but no actual files, we need to handle this differently
            if not general_documents and file_names:
                current_app.logger.warning("Have file names but no actual files - this might be from edit form")
                return
                
            if not general_documents or not doc_type_ids:
                current_app.logger.warning("No documents or document types found")
                return

            for i, doc_file in enumerate(general_documents):
                if doc_file.filename == '':
                    continue
                    
                try:
                    doc_type_id = doc_type_ids[i]
                except IndexError:
                    current_app.logger.error("Mismatched number of document files and types.")
                    continue
                    
                if doc_type_id:
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
                        doc_type_id=doc_type_id,
                        file_path=upload_path,
                        document_name=filename,
                        upload_date=datetime.now()
                    )
                    session.add(new_document)
                    current_app.logger.info(f"Saved new document for employee {employee_id} ({employee.busness_id}): {unique_filename}")
                    
                    # Process the document with AI to extract skills
                    try:
                        from processor.employee_processor import EmployeeDocumentProcessor
                        processor = EmployeeDocumentProcessor(employee_id, employee.busness_id)
                        processor.process_documents()
                        current_app.logger.info(f"Successfully processed document for employee {employee_id} ({employee.busness_id})")
                    except Exception as processing_error:
                        current_app.logger.error(f"Document processing failed for employee {employee_id}: {processing_error}")
                        # Don't fail the upload if processing fails

    except Exception as e:
        current_app.logger.error(f"File upload failed: {e}")
        # Clean up any temporary files that were already saved
        for f in temp_files:
            if os.path.exists(f):
                os.remove(f)
        raise RuntimeError(f"Could not process file uploads: {e}")