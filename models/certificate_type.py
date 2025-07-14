from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from database.connection import Base

class CertificateType(Base):
    __tablename__ = 'certificate_types'

    cert_type_id = Column(Integer, primary_key=True)
    type_name = Column(String, nullable=False)
    default_issuing_org = Column(String(255), nullable=True)
    default_validity_months = Column(Integer, nullable=True)

    documents = relationship("EmployeeDocument", back_populates="certificate_type")