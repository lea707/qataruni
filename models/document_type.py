from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from database.connection import Base

class DocumentType(Base):
    __tablename__ = 'document_types'

    type_id = Column(Integer, primary_key=True)
    doc_type_name = Column(String, nullable=False)

    documents = relationship("EmployeeDocument", back_populates="document_type")