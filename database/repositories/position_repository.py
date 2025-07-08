from models.position import Position
from database.connection import db  # db is SessionLocal

class PositionRepository:
    def get_all_positions(self):
        session = db()  # create a new session
        try:
            return session.query(Position).order_by(Position.position_name).all()
        finally:
            session.close()