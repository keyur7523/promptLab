"""API key authentication middleware."""
from fastapi import HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from typing import Optional

from app.database import get_db
from app.models.user import User

# API key header
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage."""
    return pwd_context.hash(api_key)


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """Verify an API key against its hash."""
    try:
        return pwd_context.verify(plain_key, hashed_key)
    except:
        # Fallback to simple sha256 for development
        import hashlib
        return hashlib.sha256(plain_key.encode()).hexdigest() == hashed_key


async def get_current_user(
    api_key: Optional[str] = Security(api_key_header),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to validate API key and get current user.

    Usage:
        @router.get("/protected")
        def protected_route(user: User = Depends(get_current_user)):
            return {"user_id": user.id}

    Raises:
        HTTPException: 401 if API key is invalid or missing
    """
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key",
            headers={"WWW-Authenticate": "ApiKey"}
        )

    # Query all users and check API key hash
    # Note: In production with many users, consider indexing strategy
    users = db.query(User).all()

    for user in users:
        if verify_api_key(api_key, user.api_key_hash):
            return user

    raise HTTPException(
        status_code=401,
        detail="Invalid API key",
        headers={"WWW-Authenticate": "ApiKey"}
    )


def create_user_with_api_key(db: Session, api_key: str, rate_limit: int = 100) -> User:
    """
    Helper to create a new user with an API key.

    Args:
        db: Database session
        api_key: Plain text API key (will be hashed)
        rate_limit: Requests per hour limit

    Returns:
        Created User instance
    """
    api_key_hash = hash_api_key(api_key)

    user = User(
        api_key_hash=api_key_hash,
        rate_limit=rate_limit
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
