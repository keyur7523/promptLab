"""Conversation history endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID

from app.database import get_db
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("")
async def list_conversations(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List user's conversations with preview info, newest first.

    Returns conversation id, created_at, message count, and a preview
    of the last assistant message.
    """
    # Subquery for message count per conversation
    msg_count_sub = (
        db.query(
            Message.conversation_id,
            func.count(Message.id).label("message_count"),
        )
        .group_by(Message.conversation_id)
        .subquery()
    )

    conversations = (
        db.query(Conversation)
        .filter(Conversation.user_id == user.id)
        .order_by(Conversation.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    result = []
    for conv in conversations:
        # Get message count
        count_row = (
            db.query(msg_count_sub.c.message_count)
            .filter(msg_count_sub.c.conversation_id == conv.id)
            .first()
        )
        message_count = count_row[0] if count_row else 0

        # Get first user message as preview
        first_msg = (
            db.query(Message.content)
            .filter(
                Message.conversation_id == conv.id,
                Message.role == MessageRole.USER,
            )
            .order_by(Message.created_at.asc())
            .first()
        )
        preview = ""
        if first_msg:
            preview = first_msg[0][:80] + ("..." if len(first_msg[0]) > 80 else "")

        result.append({
            "id": str(conv.id),
            "created_at": conv.created_at.isoformat(),
            "message_count": message_count,
            "preview": preview,
        })

    total = (
        db.query(func.count(Conversation.id))
        .filter(Conversation.user_id == user.id)
        .scalar()
    )

    return {"conversations": result, "total": total}


@router.get("/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all messages for a conversation, ordered chronologically."""
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == user.id)
        .first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .all()
    )

    return {
        "conversation_id": str(conversation_id),
        "messages": [
            {
                "id": str(msg.id),
                "role": msg.role.value,
                "content": msg.content,
                "variant": msg.experiment_variant,
                "model": msg.model_name,
                "tokens_in": msg.tokens_in,
                "tokens_out": msg.tokens_out,
                "latency_ms": msg.latency_ms,
                "cost": float(msg.cost) if msg.cost else None,
                "created_at": msg.created_at.isoformat(),
            }
            for msg in messages
        ],
    }


@router.delete("/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a conversation and all its messages."""
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == user.id)
        .first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    db.delete(conversation)
    db.commit()
