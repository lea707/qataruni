from models.position import Position
from database.connection import db 

class PositionRepository:
    def get_all_positions(self):
        session = db()  # create a new session
        try:
            return session.query(Position).order_by(Position.position_name).all()
        finally:
            session.close()

    # add these imports at top of position_service.py if not already present

# inside PositionService class
    def get_or_create_position(self, position_name, department_id=None):
        print("--get or create--")
        """Find a position by name (and department if provided), or create it if not exists"""
        session = db() if callable(db) else db
        try:
            query = session.query(Position).filter_by(position_name=position_name)
            if department_id:
                query = query.filter_by(department_id=department_id)

            position = query.first()
            if position:
                session.expunge(position)  # detach safely
                return position

            # Create new position if not found
            position = Position(position_name=position_name, department_id=department_id)
            session.add(position)
            session.commit()
            session.refresh(position)  # make sure attributes are loaded
            session.expunge(position)  # detach for safe return
            return position
        finally:
            if callable(db):
                session.close()
