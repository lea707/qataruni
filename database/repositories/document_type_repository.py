from models.document_type import DocumentType
from database.connection import db  # db is SessionLocal

class DocumentTypeRepository:
    def get_all_document_types(self):
        session = db()  # create a new session
        try:
            return session.query(DocumentType).order_by(DocumentType.doc_type_name).all()
        finally:
            session.close()