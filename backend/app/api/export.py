"""CSV export endpoints for experiment results and conversations."""
import csv
import io

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from datetime import datetime, timezone, timedelta

from app.database import get_db
from app.models.user import User
from app.models.message import Message, MessageRole
from app.models.feedback import Feedback
from app.models.conversation import Conversation
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/export", tags=["export"])


@router.get("/experiments")
async def export_experiment_results(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Export experiment results as CSV (variant, messages, latency, cost, approval rate)."""
    rows = (
        db.query(
            Message.experiment_variant.label("variant"),
            func.count(Message.id).label("messages"),
            func.coalesce(func.avg(Message.latency_ms), 0).label("avg_latency_ms"),
            func.coalesce(func.avg(Message.cost), 0).label("avg_cost"),
            func.coalesce(func.sum(Message.tokens_in), 0).label("total_tokens_in"),
            func.coalesce(func.sum(Message.tokens_out), 0).label("total_tokens_out"),
            func.count(Feedback.id).label("feedback_count"),
            func.sum(case((Feedback.rating == 1, 1), else_=0)).label("thumbs_up"),
            func.sum(case((Feedback.rating == -1, 1), else_=0)).label("thumbs_down"),
        )
        .outerjoin(Feedback, Message.id == Feedback.message_id)
        .join(Conversation, Message.conversation_id == Conversation.id)
        .filter(
            Conversation.user_id == user.id,
            Message.role == MessageRole.ASSISTANT,
            Message.experiment_variant.isnot(None),
        )
        .group_by(Message.experiment_variant)
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "variant", "messages", "avg_latency_ms", "avg_cost_usd",
        "total_tokens_in", "total_tokens_out",
        "feedback_count", "thumbs_up", "thumbs_down", "approval_rate",
    ])

    for row in rows:
        approval = round((row.thumbs_up or 0) / row.feedback_count * 100, 1) if row.feedback_count else 0
        writer.writerow([
            row.variant, row.messages,
            round(float(row.avg_latency_ms)), round(float(row.avg_cost), 6),
            int(row.total_tokens_in), int(row.total_tokens_out),
            row.feedback_count or 0, row.thumbs_up or 0, row.thumbs_down or 0,
            approval,
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=experiment_results.csv"},
    )


@router.get("/conversations")
async def export_conversations(
    days: int = Query(default=30, ge=1, le=365),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Export conversation transcripts as CSV."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    messages = (
        db.query(Message, Conversation.id.label("conv_id"))
        .join(Conversation, Message.conversation_id == Conversation.id)
        .filter(
            Conversation.user_id == user.id,
            Message.created_at >= cutoff,
        )
        .order_by(Conversation.created_at, Message.created_at)
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "conversation_id", "role", "content", "variant", "model",
        "prompt_version", "tokens_in", "tokens_out", "cost_usd",
        "latency_ms", "created_at",
    ])

    for msg, conv_id in messages:
        writer.writerow([
            str(conv_id), msg.role.value, msg.content,
            msg.experiment_variant or "", msg.model_name or "",
            msg.prompt_version or "", msg.tokens_in or "",
            msg.tokens_out or "", float(msg.cost) if msg.cost else "",
            msg.latency_ms or "", msg.created_at.isoformat(),
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=conversations_{days}d.csv"},
    )
