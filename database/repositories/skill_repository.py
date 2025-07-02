from database.connection import db
from models.skill import Skill

class SkillRepository:
    def get_all_skills(self):
        return db.query(Skill).order_by(Skill.skill_name).all()