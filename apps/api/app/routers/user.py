from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.db.database import get_db
from app.models.user import User, UserTier
from app.models.topic import Topic, ProcessingStatus
from app.schemas.user import (
    UserResponse,
    UserUpdate,
    UsageStats,
    PasswordChange,
)
from app.auth.dependencies import get_current_user
from app.auth.password import hash_password, verify_password


class TopicSummary(BaseModel):
    id: str
    title: str | None
    status: str
    document_count: int
    node_count: int = 0
    progress_percent: int = 0  # 0-100 based on completed nodes
    created_at: datetime
    completed_at: datetime | None
    generation_duration_seconds: float | None = None

    class Config:
        from_attributes = True

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


@router.get("/topics", response_model=List[TopicSummary])
def get_user_topics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all learning paths (topics) created by the user."""
    from app.models.topic import Document, Node, UserProgress, NodeStatus

    topics = db.query(Topic).filter(
        Topic.user_id == current_user.id
    ).order_by(Topic.created_at.desc()).all()

    result = []
    for topic in topics:
        # Count documents for this topic
        doc_count = db.query(Document).filter(Document.topic_id == topic.id).count()

        # Count nodes and completed nodes for progress
        node_count = db.query(Node).filter(Node.topic_id == topic.id).count()

        # Count completed nodes from UserProgress
        completed_count = 0
        if node_count > 0:
            # Get all node IDs for this topic
            node_ids = [n.id for n in db.query(Node.id).filter(Node.topic_id == topic.id).all()]
            # Count how many have completed status in UserProgress
            completed_count = db.query(UserProgress).filter(
                UserProgress.user_id == current_user.id,
                UserProgress.node_id.in_(node_ids),
                UserProgress.status == NodeStatus.COMPLETED,
            ).count()

        progress_percent = round((completed_count / node_count) * 100) if node_count > 0 else 0

        result.append(TopicSummary(
            id=str(topic.id),
            title=topic.title,
            status=topic.status.value,
            document_count=doc_count,
            node_count=node_count,
            progress_percent=progress_percent,
            created_at=topic.created_at,
            completed_at=topic.completed_at,
            generation_duration_seconds=topic.generation_duration_seconds,
        ))

    return result


class TopicUpdate(BaseModel):
    title: str


@router.put("/topics/{topic_id}", response_model=TopicSummary)
def update_topic(
    topic_id: str,
    update_data: TopicUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Rename a topic (learning path)."""
    topic = db.query(Topic).filter(
        Topic.id == topic_id,
        Topic.user_id == current_user.id,
    ).first()

    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found",
        )

    topic.title = update_data.title
    db.commit()
    db.refresh(topic)

    from app.models.topic import Document
    doc_count = db.query(Document).filter(Document.topic_id == topic.id).count()

    return TopicSummary(
        id=str(topic.id),
        title=topic.title,
        status=topic.status.value,
        document_count=doc_count,
        created_at=topic.created_at,
        completed_at=topic.completed_at,
        generation_duration_seconds=topic.generation_duration_seconds,
    )


@router.delete("/topics/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_topic(
    topic_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a topic and all associated data (documents, nodes, edges)."""
    topic = db.query(Topic).filter(
        Topic.id == topic_id,
        Topic.user_id == current_user.id,
    ).first()

    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found",
        )

    # Decrement user's skill_trees_created count
    if current_user.skill_trees_created > 0:
        current_user.skill_trees_created -= 1

    # Delete topic (cascade will delete documents, nodes, edges)
    db.delete(topic)
    db.commit()

    return None
