# database/connection.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, scoped_session
import os
from dotenv import load_dotenv
import sys

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Allow tests to run against a lightweight in-memory DB to avoid cross-table FK issues
if os.getenv("TEST_DATABASE_URL"):
    DATABASE_URL = os.getenv("TEST_DATABASE_URL")
elif os.getenv("TESTING") == "1" or "PYTEST_CURRENT_TEST" in os.environ:
    # Use file-based SQLite during tests to preserve schema across sessions
    DATABASE_URL = "sqlite:///test_app.db"
else:
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# SQLite needs the check_same_thread flag for in-memory use in Flask contexts
engine_kwargs = {"connect_args": {"check_same_thread": False}} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

Base = declarative_base()
db=SessionLocal

# Provide a global query property for tests using Model.query
Base.query = SessionLocal.query_property()  # type: ignore[attr-defined]