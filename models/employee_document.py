from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database.connection import Base
from datetime import datetime

class EmployeeDocument(Base):
    __tablename__ = 'employee_documents'

    document_id = Column(Integer, primary_key=True)
    cert_type_id = Column(Integer, ForeignKey('certificate_types.cert_type_id'))
    certificate_type = relationship("CertificateType", back_populates="documents")
    file_path = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow)
    expiry_date = Column(DateTime)
    employee_id = Column(Integer, ForeignKey('employee.emp_id'))
    employee = relationship("Employee", back_populates="documents")
    doc_type_id = Column(Integer, ForeignKey('document_types.type_id'))
    document_type = relationship("DocumentType", back_populates="documents")