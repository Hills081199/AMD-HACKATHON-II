from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.database import get_db
from app.models.user import User, UserRole, UserTier
from app.schemas.admin import (
    AdminUserUpdate,
    AdminUserResponse,
    AdminUserList,
    SystemStats,
)
from app.auth.dependencies import get_current_admin

router = APIRouter()


@router.get("/users", response_model=AdminUserList)
def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    tier: Optional[UserTier] = None,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    query = db.query(User)

    if search:
        query = query.filter(
            (User.email.ilike(f"%{search}%")) | (User.display_name.ilike(f"%{search}%"))
        )

    if tier:
        query = query.filter(User.tier == tier)

    total = query.count()
    users = query.offset((page - 1) * per_page).limit(per_page).all()

    return AdminUserList(
        users=[AdminUserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/users/{user_id}", response_model=AdminUserResponse)
def get_user(
    user_id: str,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return AdminUserResponse.model_validate(user)


@router.put("/users/{user_id}", response_model=AdminUserResponse)
def update_user(
    user_id: str,
    update_data: AdminUserUpdate,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if update_data.role is not None:
        user.role = update_data.role
    if update_data.tier is not None:
        user.tier = update_data.tier
    if update_data.documents_used is not None:
        user.documents_used = update_data.documents_used
    if update_data.skill_trees_created is not None:
        user.skill_trees_created = update_data.skill_trees_created

    db.commit()
    db.refresh(user)

    return AdminUserResponse.model_validate(user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: str,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if str(user.id) == str(admin.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    db.delete(user)
    db.commit()


@router.post("/users/{user_id}/reset-usage", response_model=AdminUserResponse)
def reset_user_usage(
    user_id: str,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user.documents_used = 0
    user.skill_trees_created = 0
    user.chat_messages_today = 0

    db.commit()
    db.refresh(user)

    return AdminUserResponse.model_validate(user)


@router.get("/stats", response_model=SystemStats)
def get_system_stats(
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    total_users = db.query(User).count()
    total_documents = db.query(func.sum(User.documents_used)).scalar() or 0
    total_skill_trees = db.query(func.sum(User.skill_trees_created)).scalar() or 0
    total_quizzes = db.query(func.sum(User.quizzes_completed)).scalar() or 0

    users_by_tier = {}
    for tier in UserTier:
        count = db.query(User).filter(User.tier == tier).count()
        users_by_tier[tier.value] = count

    return SystemStats(
        total_users=total_users,
        total_documents=total_documents,
        total_skill_trees=total_skill_trees,
        total_quizzes=total_quizzes,
        users_by_tier=users_by_tier,
    )
