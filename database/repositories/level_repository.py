from database.connection import db
from models.level import EmployeeLevel

class LevelRepository:
    def get_all_levels(self):
        return db.query(EmployeeLevel).order_by(EmployeeLevel.level_name).all()