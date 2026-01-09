"""Chat request/response schemas."""
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID


class ChatRequest(BaseModel):
    """Request to send a chat message."""

    message: str = Field(..., min_length=1, max_length=10000, description="User message")
    conversation_id: Optional[UUID] = Field(None, description="Existing conversation ID (optional)")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "What is the weather today?",
                "conversation_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }


class ChatResponse(BaseModel):
    """Response from chat endpoint (for non-streaming)."""

    message_id: UUID
    conversation_id: UUID
    content: str
    variant: str
    model: str

    class Config:
        json_schema_extra = {
            "example": {
                "message_id": "123e4567-e89b-12d3-a456-426614174001",
                "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
                "content": "I don't have access to real-time weather data...",
                "variant": "control",
                "model": "gpt-3.5-turbo"
            }
        }
