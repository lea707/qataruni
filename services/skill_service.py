from database.repositories.skill_repository import SkillRepository
from database.repositories.skill_category_repository import SkillCategoryRepository

class SkillService:
    def __init__(self):
        self.repository = SkillRepository()
        self.category_repository = SkillCategoryRepository()  
        self.all_skills = self.repository.get_all_skills() 

    def get_skills_by_employee(self, employee_id):
        return self.repository.get_skills_by_employee(employee_id)
    
    def get_all_skill_categories(self):
        return self.category_repository.get_all_categories()  
    def get_all_skill_levels(self):
        session = self.db()
        try:
            return self.repository.get_distinct_skill_levels(session)
        finally:
            session.close()
    def get_all_skills(self):
     return self.repository.get_all_skills()
    
    def search_skills(self, query):
        """Search skills by name (case-insensitive partial match)"""
        return self.repository.search_skills(query)