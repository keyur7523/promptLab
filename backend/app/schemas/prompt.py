"""Prompt version request/response schemas."""
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class PromptCreate(BaseModel):
    """Request to create a new prompt version."""

    variant: str = Field(..., min_length=1, max_length=50, description="Experiment variant name")
    content: str = Field(..., min_length=1, max_length=5000, description="System prompt text")


class PromptResponse(BaseModel):
    """Prompt version returned to client."""

    id: UUID
    variant: str
    version: int
    content: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
