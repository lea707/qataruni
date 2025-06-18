from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

class db_connection():
    def __init__(self):
        self.engine = create_engine('sqlite:///mydatabase.db')
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    def get_session(self):
        return self.session

    def get_engine(self):
        return self.engine
    