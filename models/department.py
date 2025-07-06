from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database.connection import Base
import uuid
from models.employee import Employee

class Department(Base):
    __tablename__ = 'departments'

    department_id = Column(Integer, primary_key=True)
    department_name = Column(String, nullable=False)
    director_emp_id = Column(Integer, ForeignKey('employee.emp_id'), nullable=True)
    director = relationship(
        "Employee",
        back_populates="directed_department",
        foreign_keys=[director_emp_id]
    )

    employees = relationship(
        "Employee",
        back_populates="department",
        foreign_keys="Employee.department_id"
    )


    parent_department_id = Column(Integer, ForeignKey('departments.department_id'), nullable=True)
    parent_department = relationship('Department', remote_side=[department_id])
    created_at = Column(DateTime, default=datetime.utcnow)
    business_id = Column(String, unique=True, default=lambda: str(uuid.uuid4()))