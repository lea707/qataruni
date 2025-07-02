from database.repositories.level_repository import LevelRepository

class LevelService:
    def __init__(self):
        self.repository = LevelRepository()

    def get_all_levels(self):
        return self.repository.get_all_levels()