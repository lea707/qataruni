from database.repositories.position_repository import PositionRepository
from database.connection import db
from models.position import Position

class PositionService:
    def __init__(self, db_session=None):  # Add db_session parameter
        self.repository = PositionRepository() 

    def get_all_positions(self):
        return self.repository.get_all_positions()

    def get_or_create_position(self, position_name, department_id=None) -> int:
        """Find a position by name (and department if provided), or create it if not exists. 
        Always returns position_id (int), never ORM object."""
        session = db() if callable(db) else db
        try:
            query = session.query(Position).filter_by(position_name=position_name)
            if department_id:
                query = query.filter_by(department_id=department_id)

            position = query.first()
            if position:
                return position

            # Create new position if not found
            position = Position(position_name=position_name, department_id=department_id)
            session.add(position)
            session.commit()
            return position 
        finally:
            if callable(db):
                session.close()
