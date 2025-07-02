from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from database.connection import Base

class EmployeeLevel(Base):
    __tablename__ = 'employee_levels'

    level_id = Column(Integer, primary_key=True)
    level_name = Column(String)
    level_rank = Column(Integer)

    employees = relationship("Employee", back_populates="level")