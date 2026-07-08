from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User, UserTier
from app.schemas.user import (
    UserResponse,
    UserUpdate,
    UsageStats,
    PasswordChange,
)
from app.auth.dependencies import get_current_user
from app.auth.password import hash_password, verify_password

router = APIRouter()

# Usage limits by tier
TIER_LIMITS = {
    UserTier.FREE: {
        "documents": 3,
        "skill_trees": 2,
        "chat_messages": 10,
    },
    UserTier.TRIAL: {
        "documents": 10,
        "skill_trees": 5,
        "chat_messages": 50,
    },
    UserTier.PREMIUM: {
        "documents": -1,  # Unlimited
        "skill_trees": -1,
        "chat_messages": -1,
    },
}


@router.get("/profile", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


@router.put("/profile", response_model=UserResponse)
def update_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if update_data.display_name is not None:
        current_user.display_name = update_data.display_name
    if update_data.avatar_url is not None:
        current_user.avatar_url = update_data.avatar_url

    db.commit()
    db.refresh(current_user)

    return UserResponse.model_validate(current_user)


@router.put("/password", status_code=status.HTTP_200_OK)
def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    current_user.password_hash = hash_password(password_data.new_password)
    db.commit()

    return {"message": "Password updated successfully"}


@router.get("/usage", response_model=UsageStats)
def get_usage(current_user: User = Depends(get_current_user)):
    limits = TIER_LIMITS.get(current_user.tier, TIER_LIMITS[UserTier.FREE])

    return UsageStats(
        documents_used=current_user.documents_used,
        documents_limit=limits["documents"],
        skill_trees_created=current_user.skill_trees_created,
        skill_trees_limit=limits["skill_trees"],
        quizzes_completed=current_user.quizzes_completed,
        chat_messages_today=current_user.chat_messages_today,
        chat_messages_limit=limits["chat_messages"],
        tier=current_user.tier.value,
    )
