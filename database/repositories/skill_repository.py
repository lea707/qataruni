from models.skill import Skill
from models.employee import Employee
from sqlalchemy.orm import joinedload
from database.connection import db 
from sqlalchemy import select, distinct
from models.associations import employee_skills


class SkillRepository:
    def get_all_skills(self):
        session = db()  # create a new session
        try:
            return session.query(Skill).order_by(Skill.skill_name).all()
        finally:
            session.close()

    def get_skills_by_employee(self, employee_id):
        session = db()
        try:
            employee = session.query(Employee).options(
                joinedload(Employee.skills)
            ).filter(Employee.emp_id == employee_id).first()
            return employee.skills if employee else []
        finally:
            session.close()
    
    def get_distinct_skill_levels(self, session):
        result = session.execute(
            select(distinct(employee_skills.c.skill_level))
            .where(employee_skills.c.skill_level.isnot(None))
            .order_by(employee_skills.c.skill_level)
        )
        return [row[0] for row in result]
    
    def search_skills(self, query):
        """Search skills by name (case-insensitive partial match)"""
        session = db()
        try:
            return session.query(Skill).filter(
                Skill.skill_name.ilike(f'%{query}%')
            ).order_by(Skill.skill_name).limit(10).all()
        finally:
            session.close()
