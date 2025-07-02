from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from database.connection import Base

class CertificateType(Base):
    __tablename__ = 'certificate_types'

    cert_type_id = Column(Integer, primary_key=True)
    type_name = Column(String, nullable=False)

    issuing_organisation = Column(String)  # Add this
    validity_period_months = Column(Integer)  # Add this

    documents = relationship("EmployeeDocument", back_populates="certificate_type")