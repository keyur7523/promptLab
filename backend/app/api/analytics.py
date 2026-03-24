"""Analytics endpoints for dashboard metrics."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case, cast, Date
from datetime import datetime, timezone, timedelta

from app.database import get_db
from app.models.user import User
from app.models.message import Message, MessageRole
from app.models.feedback import Feedback
from app.models.conversation import Conversation
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview")
async def get_overview(
    days: int = Query(default=7, ge=1, le=90),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    High-level platform statistics over a time range.

    Returns total conversations, messages, cost, latency percentiles,
    and feedback approval rate.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    # Base query: assistant messages belonging to this user within the time range
    base = (
        db.query(Message)
        .join(Conversation, Message.conversation_id == Conversation.id)
        .filter(
            Conversation.user_id == user.id,
            Message.role == MessageRole.ASSISTANT,
            Message.created_at >= cutoff,
        )
    )

    # Aggregate stats
    stats = base.with_entities(
        func.count(Message.id).label("total_messages"),
        func.count(func.distinct(Message.conversation_id)).label("total_conversations"),
        func.coalesce(func.sum(Message.cost), 0).label("total_cost"),
        func.coalesce(func.avg(Message.cost), 0).label("avg_cost"),
        func.coalesce(func.avg(Message.latency_ms), 0).label("avg_latency_ms"),
    ).first()

    # P95 latency via subquery
    latency_values = [
        row[0]
        for row in base.with_entities(Message.latency_ms)
        .filter(Message.latency_ms.isnot(None))
        .order_by(Message.latency_ms)
        .all()
    ]
    p95_latency = 0
    if latency_values:
        idx = int(len(latency_values) * 0.95)
        p95_latency = latency_values[min(idx, len(latency_values) - 1)]

    # Feedback stats
    feedback_stats = (
        db.query(
            func.count(Feedback.id).label("total_feedback"),
            func.sum(case((Feedback.rating == 1, 1), else_=0)).label("thumbs_up"),
        )
        .join(Message, Feedback.message_id == Message.id)
        .join(Conversation, Message.conversation_id == Conversation.id)
        .filter(
            Conversation.user_id == user.id,
            Feedback.created_at >= cutoff,
        )
        .first()
    )

    total_feedback = feedback_stats[0] or 0
    thumbs_up = feedback_stats[1] or 0
    approval_rate = round((thumbs_up / total_feedback * 100), 1) if total_feedback > 0 else 0

    # Total tokens
    token_stats = base.with_entities(
        func.coalesce(func.sum(Message.tokens_in), 0).label("total_tokens_in"),
        func.coalesce(func.sum(Message.tokens_out), 0).label("total_tokens_out"),
    ).first()

    return {
        "days": days,
        "total_conversations": stats[1],
        "total_messages": stats[0],
        "total_cost": round(float(stats[2]), 4),
        "avg_cost_per_message": round(float(stats[3]), 6),
        "avg_latency_ms": round(float(stats[4])),
        "p95_latency_ms": p95_latency,
        "total_tokens_in": int(token_stats[0]),
        "total_tokens_out": int(token_stats[1]),
        "total_feedback": total_feedback,
        "approval_rate": approval_rate,
    }


@router.get("/usage")
async def get_usage(
    days: int = Query(default=7, ge=1, le=90),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Daily usage time-series for charting.

    Returns per-day message count, total cost, avg latency, and total tokens.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    rows = (
        db.query(
            cast(Message.created_at, Date).label("date"),
            func.count(Message.id).label("messages"),
            func.coalesce(func.sum(Message.cost), 0).label("cost"),
            func.coalesce(func.avg(Message.latency_ms), 0).label("avg_latency_ms"),
            func.coalesce(
                func.sum(Message.tokens_in) + func.sum(Message.tokens_out), 0
            ).label("tokens_total"),
        )
        .join(Conversation, Message.conversation_id == Conversation.id)
        .filter(
            Conversation.user_id == user.id,
            Message.role == MessageRole.ASSISTANT,
            Message.created_at >= cutoff,
        )
        .group_by(cast(Message.created_at, Date))
        .order_by(cast(Message.created_at, Date))
        .all()
    )

    return {
        "days": days,
        "usage": [
            {
                "date": row.date.isoformat(),
                "messages": row.messages,
                "cost": round(float(row.cost), 4),
                "avg_latency_ms": round(float(row.avg_latency_ms)),
                "tokens_total": int(row.tokens_total),
            }
            for row in rows
        ],
    }


@router.get("/experiments")
async def get_experiments(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Experiment variant performance comparison.

    Returns per-variant message count, avg latency, avg cost,
    approval rate, and sample size.
    """
    rows = (
        db.query(
            Message.experiment_variant.label("variant"),
            func.count(Message.id).label("messages"),
            func.coalesce(func.avg(Message.latency_ms), 0).label("avg_latency_ms"),
            func.coalesce(func.avg(Message.cost), 0).label("avg_cost"),
            func.count(Feedback.id).label("feedback_count"),
            func.sum(case((Feedback.rating == 1, 1), else_=0)).label("thumbs_up"),
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

    return {
        "experiments": [
            {
                "variant": row.variant,
                "messages": row.messages,
                "avg_latency_ms": round(float(row.avg_latency_ms)),
                "avg_cost": round(float(row.avg_cost), 6),
                "approval_rate": (
                    round((row.thumbs_up or 0) / row.feedback_count * 100, 1)
                    if row.feedback_count
                    else 0
                ),
                "sample_size": row.feedback_count or 0,
            }
            for row in rows
        ],
    }


@router.get("/latency")
async def get_latency_distribution(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Latency distribution bucketed into ranges.

    Returns count of messages per latency bucket.
    """
    buckets = [
        ("0-500ms", 0, 500),
        ("500ms-1s", 500, 1000),
        ("1-2s", 1000, 2000),
        ("2-5s", 2000, 5000),
        ("5s+", 5000, None),
    ]

    base = (
        db.query(Message.latency_ms)
        .join(Conversation, Message.conversation_id == Conversation.id)
        .filter(
            Conversation.user_id == user.id,
            Message.role == MessageRole.ASSISTANT,
            Message.latency_ms.isnot(None),
        )
    )

    result = []
    for label, low, high in buckets:
        q = base
        q = q.filter(Message.latency_ms >= low)
        if high is not None:
            q = q.filter(Message.latency_ms < high)
        count = q.count()
        result.append({"bucket": label, "count": count})

    return {"distribution": result}
