"""API key authentication middleware.

Uses SHA256 hashing for API keys with direct database lookup.
This provides O(1) lookup time vs the previous O(n) approach.

Note: API keys use SHA256 (not bcrypt) because:
- API keys are high-entropy random strings, not user-chosen passwords
- Brute-force protection comes from key length (32+ chars), not hash slowness
- Fast lookup is critical for every authenticated request
- The api_key_hash column is indexed for O(1) database lookup
"""
import hashlib
from fastapi import HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.user import User

# API key header
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)


def hash_api_key(api_key: str) -> str:
    """
    Hash an API key for storage using SHA256.

    SHA256 is appropriate for API keys because:
    - Deterministic: same input always produces same hash (required for lookup)
    - Fast: O(1) verification via direct database query on indexed column
    - Secure: API keys are randomly generated with high entropy

    Args:
        api_key: Plain text API key

    Returns:
        SHA256 hex digest of the API key
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


async def get_current_user(
    api_key: Optional[str] = Security(api_key_header),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to validate API key and get current user.

    Uses direct database lookup by hashed API key for O(1) performance.
    The api_key_hash column is indexed, making this query fast even with
    millions of users.

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

    # Hash the provided API key and lookup directly by hash
    # This is O(1) with the indexed api_key_hash column
    api_key_hash = hash_api_key(api_key)

    user = db.query(User).filter(
        User.api_key_hash == api_key_hash
    ).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"}
        )

    return user


def create_user_with_api_key(db: Session, api_key: str, rate_limit: int = 100) -> User:
    """
    Helper to create a new user with an API key.

    Args:
        db: Database session
        api_key: Plain text API key (will be hashed with SHA256)
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
