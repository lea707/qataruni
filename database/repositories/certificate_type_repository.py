from models.certificate_type import CertificateType
from database.connection import db  # now this is SessionLocal

class CertificateTypeRepository:
    def get_all_certificate_types(self):
        session = db()  # create a new session
        try:
            return session.query(CertificateType).order_by(CertificateType.type_name).all()
        finally:
            session.close()