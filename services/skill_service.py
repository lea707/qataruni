from database.repositories.skill_repository import SkillRepository

class SkillService:
    def __init__(self):
        self.repository = SkillRepository()

    def get_all_skills(self):
        return self.repository.get_all_skills()

    def get_skills_by_employee(self, employee_id):
        return self.repository.get_skills_by_employee(employee_id)