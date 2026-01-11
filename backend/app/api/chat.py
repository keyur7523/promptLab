"""Chat endpoints with streaming support."""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Dict
import json
import redis

from app.database import get_db
from app.schemas.chat import ChatRequest
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from app.middleware.auth import get_current_user
from app.middleware.logging import get_logger
from app.services.llm import LLMService
from app.services.experiments import ExperimentService
from app.services.rate_limiter import RateLimiter
from app.services.token_counter import get_token_counter
from app.config import get_settings

router = APIRouter()
settings = get_settings()
logger = get_logger()

# Initialize services
token_counter = get_token_counter(
    base_url=settings.token_counter_url,
    timeout=settings.token_counter_timeout,
    enabled=settings.token_counter_enabled
)
llm_service = LLMService(
    api_key=settings.openai_api_key,
    token_counter=token_counter
)
redis_client = redis.from_url(settings.redis_url)
rate_limiter = RateLimiter(redis_client)


def get_or_create_conversation(
    db: Session,
    conversation_id: str | None,
    user_id: str
) -> Conversation:
    """Get existing conversation or create new one."""
    if conversation_id:
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        ).first()

        if not conversation:
            raise HTTPException(404, "Conversation not found")

        return conversation

    # Create new conversation
    conversation = Conversation(user_id=user_id)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def get_conversation_history(db: Session, conversation_id: str, limit: int = 10) -> List[Dict]:
    """Get recent messages from conversation for context."""
    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at.desc()).limit(limit).all()

    # Reverse to chronological order
    messages = list(reversed(messages))

    return [
        {"role": msg.role.value, "content": msg.content}
        for msg in messages
    ]


def get_prompt_for_variant(variant: str) -> str:
    """Get system prompt based on experiment variant."""
    prompts = {
        "control": "You are a helpful AI assistant. Provide detailed and informative responses.",
        "concise": "You are a helpful AI assistant. Be concise and to the point.",
        "friendly": "You are a friendly and enthusiastic AI assistant. Be warm and encouraging!",
    }
    return prompts.get(variant, prompts["control"])


@router.post("/chat")
async def chat(
    request: Request,
    chat_request: ChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Chat endpoint with Server-Sent Events (SSE) streaming.

    Returns a stream of tokens from the LLM in real-time.

    Example SSE events:
        data: {"token": "Hello"}
        data: {"token": " there!"}
        data: {"done": true, "message_id": "uuid", "metadata": {...}}
    """
    trace_id = request.state.trace_id

    # Rate limiting
    allowed, count = rate_limiter.check_rate_limit(
        str(user.id),
        limit=user.rate_limit,
        window=settings.rate_limit_window
    )

    if not allowed:
        logger.warning("rate_limit_exceeded", user_id=str(user.id), count=count)
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Limit: {user.rate_limit} requests per hour",
            headers={"X-RateLimit-Limit": str(user.rate_limit), "X-RateLimit-Remaining": "0"}
        )

    logger.info(
        "chat_request_received",
        user_id=str(user.id),
        conversation_id=str(chat_request.conversation_id) if chat_request.conversation_id else None,
        message_length=len(chat_request.message)
    )

    # Get or create conversation
    conversation = get_or_create_conversation(
        db,
        str(chat_request.conversation_id) if chat_request.conversation_id else None,
        str(user.id)
    )

    # Assign experiment variant
    experiment_service = ExperimentService(db)
    variant = experiment_service.assign_variant(
        str(user.id),
        "prompt_experiment_jan2024"
    )

    logger.info(
        "experiment_variant_assigned",
        user_id=str(user.id),
        variant=variant
    )

    # Build prompt based on variant
    system_prompt = get_prompt_for_variant(variant)

    # Get conversation history
    history = get_conversation_history(db, str(conversation.id))

    # Build messages for LLM
    messages = [
        {"role": "system", "content": system_prompt},
        *history,
        {"role": "user", "content": chat_request.message}
    ]

    # Save user message
    user_message = Message(
        conversation_id=conversation.id,
        role=MessageRole.USER,
        content=chat_request.message
    )
    db.add(user_message)
    db.commit()

    # Extract conversation_id before entering generator
    # (to avoid accessing detached ORM object after session closes)
    conversation_id = str(conversation.id)

    # Pre-estimate tokens (demonstrates Rust integration)
    estimated_tokens = await llm_service.pre_estimate_tokens(messages, "gpt-3.5-turbo")
    logger.info(
        "pre_estimated_tokens",
        estimated_tokens=estimated_tokens,
        message_count=len(messages)
    )

    # Stream response
    async def event_stream():
        full_content = ""
        metadata = {}

        try:
            logger.info("llm_call_started", model="gpt-3.5-turbo", message_count=len(messages))

            async for token, meta in llm_service.stream_chat(messages, model="gpt-3.5-turbo"):
                if token:
                    # Stream token to client
                    full_content += token
                    yield f"data: {json.dumps({'token': token})}\n\n"

                if meta.get("done"):
                    metadata = meta

            # Create new database session for saving assistant message
            # (original session from dependency injection is closed)
            from app.database import SessionLocal
            db_new = SessionLocal()

            try:
                # Save assistant message with metadata
                assistant_message = Message(
                    conversation_id=conversation_id,
                    role=MessageRole.ASSISTANT,
                    content=metadata.get("full_content", full_content),
                    experiment_variant=variant,
                    model_name=metadata.get("model", "gpt-3.5-turbo"),
                    prompt_version="v1",
                    tokens_in=metadata.get("tokens_in"),
                    tokens_out=metadata.get("tokens_out"),
                    cost=metadata.get("cost"),
                    latency_ms=metadata.get("latency_ms")
                )
                db_new.add(assistant_message)
                db_new.commit()
                db_new.refresh(assistant_message)

                logger.info(
                    "llm_call_completed",
                    message_id=str(assistant_message.id),
                    tokens_in=metadata.get("tokens_in"),
                    tokens_out=metadata.get("tokens_out"),
                    latency_ms=metadata.get("latency_ms"),
                    cost=metadata.get("cost")
                )

                # Send final metadata to client
                final_data = {
                    "done": True,
                    "message_id": str(assistant_message.id),
                    "conversation_id": conversation_id,
                    "variant": variant,
                    "model": metadata.get("model", "gpt-3.5-turbo"),
                    "tokens_in": metadata.get("tokens_in"),
                    "tokens_out": metadata.get("tokens_out"),
                    "latency_ms": metadata.get("latency_ms"),
                    "cost": metadata.get("cost")
                }
                yield f"data: {json.dumps(final_data)}\n\n"

            finally:
                db_new.close()

        except Exception as e:
            logger.error(
                "llm_call_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            # Send error to client
            yield f"data: {json.dumps({'error': 'Failed to get response from LLM'})}\n\n"

    # Set rate limit headers
    remaining = rate_limiter.get_remaining(str(user.id), user.rate_limit, settings.rate_limit_window)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "X-RateLimit-Limit": str(user.rate_limit),
            "X-RateLimit-Remaining": str(remaining)
        }
    )
