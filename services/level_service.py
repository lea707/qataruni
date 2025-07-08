from database.repositories.level_repository import LevelRepository

class LevelService:
   def __init__(self, db_session=None):  # Add db_session parameter
        self.repository = LevelRepository()
   def get_all_levels(self):
        return self.repository.get_all_levels()