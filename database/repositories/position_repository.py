from database.connection import db
from models.position import Position

class PositionRepository:
    def get_all_positions(self):
        return db.query(Position).order_by(Position.position_name).all()