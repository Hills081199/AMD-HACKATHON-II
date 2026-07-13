from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel

from app.models.user import UserRole, UserTier


class AdminUserUpdate(BaseModel):
    role: Optional[UserRole] = None
    tier: Optional[UserTier] = None
    documents_used: Optional[int] = None
    skill_trees_created: Optional[int] = None


class AdminUserResponse(BaseModel):
    id: UUID
    email: str
    display_name: Optional[str]
    role: str
    tier: str
    created_at: datetime
    last_login_at: Optional[datetime]
    documents_used: int
    skill_trees_created: int
    quizzes_completed: int

    class Config:
        from_attributes = True


class AdminUserList(BaseModel):
    users: List[AdminUserResponse]
    total: int
    page: int
    per_page: int


class SystemStats(BaseModel):
    total_users: int
    total_documents: int
    total_skill_trees: int
    total_quizzes: int
    users_by_tier: dict
