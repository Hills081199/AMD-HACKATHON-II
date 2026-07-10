import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Load .env from project root
load_dotenv(os.path.join(os.path.dirname(__file__), "../../../../.env"))

# Default to SQLite (no server needed). Override with DB_URL in .env for Postgres.
_default_db = "sqlite:///" + os.path.join(os.path.dirname(__file__), "../../../../atlas.db")
DATABASE_URL = os.getenv("DB_URL", _default_db)

# SQLite needs check_same_thread=False for FastAPI's multi-thread usage
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
