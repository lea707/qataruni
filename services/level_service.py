from database.repositories.level_repository import LevelRepository
from database.connection import db
from models.level import EmployeeLevel

class LevelService:
    def __init__(self, db_session=None):  # Add db_session parameter
        self.repository = LevelRepository()

    def get_all_levels(self):
        return self.repository.get_all_levels()

    def get_highest_level(self):
        session = db() if callable(db) else db
        try:
            return session.query(EmployeeLevel).order_by(EmployeeLevel.level_rank.desc()).first()
        finally:
            if callable(db):
                session.close()

    def get_lowest_level(self):
        """Return the level with the lowest rank."""
        session = db() if callable(db) else db
        try:
            return session.query(EmployeeLevel).order_by(EmployeeLevel.level_rank.asc()).first()
        finally:
            if callable(db):
                session.close()
