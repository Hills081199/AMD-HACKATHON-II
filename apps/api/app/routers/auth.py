from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    PasswordResetRequest,
)
from app.auth.password import hash_password, verify_password
from app.auth.jwt import create_access_token

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create new user
    user = User(
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        display_name=user_data.display_name,
        last_login_at=datetime.utcnow(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Generate token
    access_token = create_access_token(user.id, user.role.value)

    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()

    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Update last login
    user.last_login_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    # Generate token
    access_token = create_access_token(user.id, user.role.value)

    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
def forgot_password(request: PasswordResetRequest, db: Session = Depends(get_db)):
    # Always return success to prevent email enumeration
    user = db.query(User).filter(User.email == request.email).first()

    if user:
        # TODO: Generate reset token and send email
        # For hackathon demo, just log it
        pass

    return {"message": "If email exists, a reset link has been sent"}


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout():
    # JWT tokens are stateless, client should just discard the token
    return {"message": "Logged out successfully"}
