import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Load .env from project root
load_dotenv(os.path.join(os.path.dirname(__file__), "../../../../.env"))

DATABASE_URL = os.getenv("DB_URL", "postgresql://postgres:postgres@localhost:5432/atlas")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
