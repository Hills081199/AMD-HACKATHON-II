import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.db.database import Base, GUID


class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"


class UserTier(str, enum.Enum):
    FREE = "free"
    TRIAL = "trial"
    PREMIUM = "premium"


class User(Base):
    __tablename__ = "users"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(100), nullable=True)
    avatar_url = Column(String(500), nullable=True)

    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    tier = Column(SQLEnum(UserTier), default=UserTier.FREE, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)

    trial_started_at = Column(DateTime, nullable=True)
    trial_expires_at = Column(DateTime, nullable=True)

    # Usage tracking
    documents_used = Column(Integer, default=0)
    documents_reset_at = Column(DateTime, nullable=True)
    skill_trees_created = Column(Integer, default=0)
    quizzes_completed = Column(Integer, default=0)
    chat_messages_today = Column(Integer, default=0)
    chat_reset_at = Column(DateTime, nullable=True)

    # Relationships
    topics = relationship("Topic", back_populates="user")


class PasswordReset(Base):
    __tablename__ = "password_resets"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, nullable=False, index=True)
    token_hash = Column(String(255), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
