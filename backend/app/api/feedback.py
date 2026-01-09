"""Feedback endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.feedback import FeedbackRequest, FeedbackResponse
from app.models.user import User
from app.models.message import Message
from app.models.feedback import Feedback
from app.models.conversation import Conversation
from app.middleware.auth import get_current_user
from app.middleware.logging import get_logger

router = APIRouter()
logger = get_logger()


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    feedback_request: FeedbackRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit feedback (thumbs up/down) for an assistant message.

    - Validates that the message exists and belongs to the user
    - Prevents duplicate feedback on the same message
    - Logs feedback for analytics
    """
    # Validate message exists and belongs to user
    message = db.query(Message).join(Conversation).filter(
        Message.id == feedback_request.message_id,
        Conversation.user_id == user.id
    ).first()

    if not message:
        logger.warning(
            "feedback_invalid_message",
            user_id=str(user.id),
            message_id=str(feedback_request.message_id)
        )
        raise HTTPException(
            status_code=404,
            detail="Message not found or does not belong to you"
        )

    # Check if feedback already exists
    existing_feedback = db.query(Feedback).filter(
        Feedback.message_id == feedback_request.message_id
    ).first()

    if existing_feedback:
        # Update existing feedback
        existing_feedback.rating = feedback_request.rating
        existing_feedback.comment = feedback_request.comment
        db.commit()

        logger.info(
            "feedback_updated",
            user_id=str(user.id),
            message_id=str(feedback_request.message_id),
            rating=feedback_request.rating,
            variant=message.experiment_variant
        )

        return FeedbackResponse(
            status="success",
            message="Feedback updated"
        )

    # Create new feedback
    feedback = Feedback(
        message_id=feedback_request.message_id,
        rating=feedback_request.rating,
        comment=feedback_request.comment
    )
    db.add(feedback)
    db.commit()

    logger.info(
        "feedback_received",
        user_id=str(user.id),
        message_id=str(feedback_request.message_id),
        rating=feedback_request.rating,
        variant=message.experiment_variant,
        has_comment=bool(feedback_request.comment)
    )

    return FeedbackResponse(
        status="success",
        message="Feedback recorded"
    )


@router.get("/feedback/stats")
async def get_feedback_stats(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get feedback statistics (admin/analytics endpoint).

    Returns aggregated stats by experiment variant.
    """
    # This is a simple example - in production you'd want more sophisticated analytics
    from sqlalchemy import func

    stats = db.query(
        Message.experiment_variant,
        func.count(Feedback.id).label('total_feedback'),
        func.sum(func.case((Feedback.rating == 1, 1), else_=0)).label('thumbs_up'),
        func.sum(func.case((Feedback.rating == -1, 1), else_=0)).label('thumbs_down')
    ).outerjoin(Feedback, Message.id == Feedback.message_id)\
     .join(Conversation, Message.conversation_id == Conversation.id)\
     .filter(Conversation.user_id == user.id)\
     .group_by(Message.experiment_variant)\
     .all()

    result = []
    for variant, total, thumbs_up, thumbs_down in stats:
        if variant:  # Skip messages without variants
            approval_rate = (thumbs_up / total * 100) if total > 0 else 0
            result.append({
                "variant": variant,
                "total_feedback": total or 0,
                "thumbs_up": thumbs_up or 0,
                "thumbs_down": thumbs_down or 0,
                "approval_rate": round(approval_rate, 2)
            })

    return {"stats": result}
