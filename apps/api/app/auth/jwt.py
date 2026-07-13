import os
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from jose import JWTError, jwt

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_DAYS = int(os.getenv("JWT_EXPIRATION_DAYS", "7"))


def create_access_token(user_id: UUID, role: str) -> str:
    expire = datetime.utcnow() + timedelta(days=JWT_EXPIRATION_DAYS)
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None
