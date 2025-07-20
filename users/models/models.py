from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship, declarative_base
from database.connection import engine

Base = declarative_base()

# Association table for many-to-many between roles and permissions
role_permission = Table(
    'role_permission', Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.role_id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.permission_id'), primary_key=True)
)

class Role(Base):
    __tablename__ = 'roles'
    role_id = Column(Integer, primary_key=True)
    role_name = Column(String, nullable=False, unique=True)
    description = Column(String)
    permissions = relationship('Permission', secondary=role_permission, back_populates='roles')

class Permission(Base):
    __tablename__ = 'permissions'
    permission_id = Column(Integer, primary_key=True)
    permission_name = Column(String, nullable=False, unique=True)
    description = Column(String)
    roles = relationship('Role', secondary=role_permission, back_populates='permissions')

class User(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    emp_id = Column(Integer)  # FK to employee table if needed
    role_id = Column(Integer, ForeignKey('roles.role_id'))
    role = relationship('Role')
    last_login = Column(String)
    business_user_id = Column(String)
    email = Column(String, unique=True)
    phone_number = Column(String)