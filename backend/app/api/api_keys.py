"""API key management endpoints."""
import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.middleware.auth import get_current_user, hash_api_key

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


@router.get("/me")
async def get_current_key_info(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get info about the current API key (usage stats, not the key itself)."""
    conversation_count = (
        db.query(func.count(Conversation.id))
        .filter(Conversation.user_id == user.id)
        .scalar()
    )
    message_count = (
        db.query(func.count(Message.id))
        .join(Conversation)
        .filter(Conversation.user_id == user.id)
        .scalar()
    )

    return {
        "user_id": str(user.id),
        "rate_limit": user.rate_limit,
        "created_at": user.created_at.isoformat(),
        "conversations": conversation_count,
        "messages": message_count,
        "key_prefix": user.api_key_hash[:8] + "...",
    }


@router.post("/rotate")
async def rotate_api_key(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Rotate the current API key.

    Generates a new key and invalidates the old one.
    The new key is returned once — save it immediately.
    """
    new_key = f"pk-{secrets.token_urlsafe(32)}"
    user.api_key_hash = hash_api_key(new_key)
    db.commit()

    return {
        "status": "success",
        "api_key": new_key,
        "note": "Save this key! The old key is now invalid. This is the only time the new key will be shown.",
    }


@router.post("/generate")
async def generate_new_key(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate a new API key (creates a new user).

    Useful for creating separate keys for different environments or team members.
    """
    new_key = f"pk-{secrets.token_urlsafe(32)}"
    new_user = User(
        api_key_hash=hash_api_key(new_key),
        rate_limit=user.rate_limit,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "status": "success",
        "user_id": str(new_user.id),
        "api_key": new_key,
        "note": "Save this key! This is the only time it will be shown.",
    }
