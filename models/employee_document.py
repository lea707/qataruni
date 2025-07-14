from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Date
from sqlalchemy.orm import relationship
from database.connection import Base
from datetime import datetime
from models.certificate_type import CertificateType

class EmployeeDocument(Base):
    __tablename__ = 'employee_documents'

    document_id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employee.emp_id'), nullable=False)
    doc_type_id = Column(Integer, ForeignKey('document_types.type_id'), nullable=True)
    cert_type_id = Column(Integer, ForeignKey('certificate_types.cert_type_id'), nullable=True)
    document_name = Column(Text, nullable=False)
    upload_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=True)
    file_path = Column(Text, nullable=True)
    
    skill_name = Column(String, nullable=True)
    issuing_organization = Column(String(255), nullable=True)
    validity_period_months = Column(Integer, nullable=True)

    employee = relationship("Employee", back_populates="documents")
    document_type = relationship("DocumentType", back_populates="documents")
    certificate_type = relationship("CertificateType", back_populates="documents")