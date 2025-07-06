from database.connection import db
from models.skill import Skill
from models.employee import Employee
from sqlalchemy.orm import joinedload

class SkillRepository:
    def get_all_skills(self):
        return db.query(Skill).order_by(Skill.skill_name).all()

    def get_skills_by_employee(self, employee_id):
        employee = db.query(Employee).options(
            joinedload(Employee.skills)
        ).filter(Employee.emp_id == employee_id).first()
        return employee.skills if employee else []