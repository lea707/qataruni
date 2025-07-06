from database.repositories.position_repository import PositionRepository

class PositionService:
    def __init__(self):
        self.repository = PositionRepository()

    def get_all_positions(self):
        return self.repository.get_all_positions()