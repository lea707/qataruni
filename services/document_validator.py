# services/document_validator.py
from flask import current_app

class DocumentValidator:
    @staticmethod
    def validate_document_data(document_data: dict) -> tuple[bool, str]:
        """
        Validate document data before insertion
        Returns (is_valid, error_message)
        """
        # Check if it's a certificate document
        is_certificate = (
            document_data.get('cert_type_id') is not None or
            document_data.get('document_name', '').lower() == 'certificate' or
            document_data.get('skill_name') is not None
        )
        
        # Check if it's a general document
        is_general = document_data.get('doc_type_id') is not None
        
        if is_certificate and is_general:
            return False, "Document cannot be both a certificate and general document"
        
        if is_certificate:
            # Validate certificate requirements
            if not document_data.get('cert_type_id'):
                return False, "Certificate documents require cert_type_id"
            return True, ""
        
        if is_general:
            # Validate general document requirements
            if not document_data.get('doc_type_id'):
                return False, "General documents require doc_type_id"
            return True, ""
        
        # Neither type specified
        return False, "Document must have either doc_type_id (general) or cert_type_id (certificate)"

    @staticmethod
    def prepare_document_data(form_data: dict, files: dict, is_certificate: bool = False) -> dict:
        """
        Prepare and validate document data from form
        """
        data = {
            'document_name': form_data.get('document_name', ''),
            'upload_date': form_data.get('upload_date'),
            'file_path': form_data.get('file_path'),
            'skill_name': form_data.get('skill_name'),
            'issuing_organization': form_data.get('issuing_organization'),
            'validity_period_months': form_data.get('validity_period_months')
        }
        
        if is_certificate:
            data['cert_type_id'] = form_data.get('certificate_type_id')
            # Set default certificate name if not provided
            if not data['document_name']:
                data['document_name'] = 'certificate'
        else:
            data['doc_type_id'] = form_data.get('document_type_id')
        
        return data