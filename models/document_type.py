from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from database.connection import Base

class DocumentType(Base):
    __tablename__ = 'document_types'

    type_id = Column(Integer, primary_key=True)
    # Keep backward compatibility: accept both 'doc_type_name' and 'type_name' at init
    doc_type_name = Column(String, nullable=False)

    def __init__(self, *args, **kwargs):
        # Map legacy key 'type_name' to 'doc_type_name'
        if 'type_name' in kwargs and 'doc_type_name' not in kwargs:
            kwargs['doc_type_name'] = kwargs.pop('type_name')
        super().__init__(*args, **kwargs)

    documents = relationship("EmployeeDocument", back_populates="document_type")