from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os

# Using SQLite for instant local hackathon testing. 
# For production/submission, swap to: "postgresql://user:password@localhost/internloom"
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./internloom.db")

# check_same_thread is required only for SQLite
connect_args = {"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency for FastAPI to yield db sessions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()