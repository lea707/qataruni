from database.connection import db
from models.document_type import DocumentType

class DocumentTypeRepository:
    def get_all_document_types(self):
        return db.query(DocumentType).order_by(DocumentType.doc_type_name).all()