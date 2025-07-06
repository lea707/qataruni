from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database.connection import Base
from .associations import employee_skills 
class Skill(Base):
    __tablename__ = 'skills'

    skill_id = Column(Integer, primary_key=True)
    skill_name = Column(String, nullable=False)
    category_id = Column(Integer, ForeignKey('skill_categories.category_id'))
    employees = relationship(
        "Employee",
        secondary=employee_skills,
        back_populates="skills"
    )
    category = relationship("SkillCategory", back_populates="skills")