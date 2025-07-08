from sqlalchemy import Column, Integer, String, Boolean, Date, ForeignKey, Table
from database.connection import Base

employee_skills = Table(
    'employee_skills',
    Base.metadata,
    Column('employee_id', Integer, ForeignKey('employee.emp_id'), primary_key=True),
    Column('skill_id', Integer, ForeignKey('skills.skill_id'), primary_key=True),
    Column('skill_level', String),  
    Column('certified', Boolean, default=False), 
    Column('years_experience', Integer),          
    Column('last_used_date', Date)               
)