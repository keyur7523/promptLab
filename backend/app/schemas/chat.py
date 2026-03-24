"""Chat request schema."""
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
