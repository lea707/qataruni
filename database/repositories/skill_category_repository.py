from models.skill_category import SkillCategory
from database.connection import db  # db is SessionLocal

class SkillCategoryRepository:
    def get_all_categories(self):
        session = db()  # create a new session
        try:
            return session.query(SkillCategory).order_by(SkillCategory.category_name).all()
        finally:
            session.close()