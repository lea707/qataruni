from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database.connection import Base

class Skill(Base):
    __tablename__ = 'skills'

    skill_id = Column(Integer, primary_key=True)
    skill_name = Column(String, nullable=False)
    category_id = Column(Integer, ForeignKey('skill_categories.category_id'))

    category = relationship("SkillCategory", back_populates="skills")

    def __repr__(self):
        return f"<Skill(id={self.skill_id}, name='{self.skill_name}')>"
    
