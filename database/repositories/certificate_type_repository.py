from database.connection import db
from models.certificate_type import CertificateType

class CertificateTypeRepository:
    def get_all_certificate_types(self):
        return db.query(CertificateType).order_by(CertificateType.type_name).all()