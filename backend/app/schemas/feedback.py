"""Feedback request/response schemas."""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from uuid import UUID


class FeedbackRequest(BaseModel):
    """Request to submit feedback on a message."""

    message_id: UUID = Field(..., description="ID of the assistant message")
    rating: Literal[1, -1] = Field(..., description="1 for thumbs up, -1 for thumbs down")
    comment: Optional[str] = Field(None, max_length=1000, description="Optional comment")

    @field_validator('rating')
    @classmethod
    def validate_rating(cls, v):
        if v not in [1, -1]:
            raise ValueError('rating must be 1 or -1')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "message_id": "123e4567-e89b-12d3-a456-426614174001",
                "rating": 1,
                "comment": "Very helpful response!"
            }
        }


class FeedbackResponse(BaseModel):
    """Response after submitting feedback."""

    status: str = Field(default="success")
    message: str = Field(default="Feedback recorded")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Feedback recorded"
            }
        }
