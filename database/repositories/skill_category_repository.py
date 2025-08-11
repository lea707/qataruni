from models.skill_category import SkillCategory
from database.connection import db  # db is SessionLocal

class SkillCategoryRepository:
    def get_all_categories(self):
        session = db()  # create a new session
        try:
            return session.query(SkillCategory).order_by(SkillCategory.category_name).all()
        finally:
            session.close()
    def get_by_name(self, category_name):
        session = db()
        try:
            return session.query(SkillCategory).filter(
                SkillCategory.category_name.ilike(category_name)
            ).first()
        finally:
            session.close()
    
    def get_or_create_category(self, category_name):
        session = db()
        try:
            category = self.get_by_name(category_name)
            if not category:
                category = SkillCategory(category_name=category_name)
                session.add(category)
                session.flush()
            return category
        finally:
            session.close()