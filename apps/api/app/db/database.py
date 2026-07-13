import os
import uuid
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID as pgUUID

# Load .env from project root
load_dotenv(os.path.join(os.path.dirname(__file__), "../../../../.env"))

# Default to SQLite (no server needed). Override with DB_URL in .env for Postgres.
_default_db = "sqlite:///" + os.path.join(os.path.dirname(__file__), "../../../../atlas.db")
DATABASE_URL = os.getenv("DB_URL", _default_db)

class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses CHAR(36), storing as string.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(pgUUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                try:
                    return str(uuid.UUID(value))
                except ValueError:
                    return str(value)
            else:
                return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                try:
                    return uuid.UUID(value)
                except ValueError:
                    return value
            return value

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
