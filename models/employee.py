from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from database.connection import Base
from .associations import employee_skills  


class Employee(Base):
    __tablename__ = 'employee'

    emp_id = Column(Integer, primary_key=True)
    email = Column(Text)
    phone = Column(String)
    position_id = Column(Integer, ForeignKey('positions.position_id'))
    hire_date = Column(Date)
    supervisor_emp_id = Column(Integer, ForeignKey('employee.emp_id'))
    is_active = Column(Boolean)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    busness_id = Column(String, unique=True, nullable=False)
    arab_name = Column(String)
    english_name = Column(String)
    department_id = Column(Integer, ForeignKey('departments.department_id'))
    level_id = Column(Integer, ForeignKey('employee_levels.level_id'))
    level = relationship("EmployeeLevel", back_populates="employees")
    skills = relationship(
    "Skill",
    secondary=employee_skills,
    back_populates="employees"
)

    department = relationship(
    "Department",
    back_populates="employees",
    foreign_keys=[department_id]
)
    directed_department = relationship(
    "Department",
    back_populates="director",
    uselist=False,
    foreign_keys="[Department.director_emp_id]"
)
    position = relationship("Position", back_populates="employees")
    documents = relationship("EmployeeDocument", back_populates="employee")

    @property
    def department_name(self):
        return self.department.name if self.department else "—"

    @property
    def position_name(self):
        return self.position.name if self.position else "—"

    @property
    def level_name(self):
        return self.level.name if self.level else "—"
    def __repr__(self):
     return f"<Employee(id={self.emp_id}, name='{self.english_name}')>"