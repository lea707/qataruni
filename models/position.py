from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey, Boolean
from database.connection import Base

class Position(Base):
    __tablename__ = 'positions'

    position_id = Column(Integer, primary_key=True)
    position_name = Column(String)
    department_id = Column(Integer, ForeignKey('departments.department_id'))
    is_active = Column(Boolean)

    employees = relationship("Employee", back_populates="position")