from sqlalchemy import Table, Column, Integer, ForeignKey
from database.connection import Base

employee_skills = Table(
    'employee_skills',
    Base.metadata,
    Column('employee_id', Integer, ForeignKey('employee.emp_id'), primary_key=True),
    Column('skill_id', Integer, ForeignKey('skills.skill_id'), primary_key=True)
)