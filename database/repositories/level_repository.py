from models.level import EmployeeLevel
from database.connection import SessionLocal

class LevelRepository:
    def get_all_levels(self):
        session = SessionLocal()
        try:
            return session.query(EmployeeLevel).order_by(EmployeeLevel.level_name).all()
        finally:
            session.close()