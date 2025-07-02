from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from database.connection import Base

class SkillCategory(Base):
    __tablename__ = 'skill_categories'

    category_id = Column(Integer, primary_key=True)
    category_name = Column(String, nullable=False)

    skills = relationship("Skill", back_populates="category")

    def __repr__(self):
        return f"<SkillCategory(id={self.category_id}, name='{self.category_name}')>"