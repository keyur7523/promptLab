"""Experiment request/response schemas."""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict
from uuid import UUID
from datetime import datetime


class ExperimentCreate(BaseModel):
    """Request to create a new experiment."""

    key: str = Field(..., min_length=1, max_length=100, description="Unique experiment identifier")
    description: str = Field("", max_length=500, description="Human-readable description")
    variants: Dict[str, int] = Field(..., description="Variant names mapped to weights (must sum to 100)")

    @field_validator("variants")
    @classmethod
    def validate_variants(cls, v: Dict[str, int]) -> Dict[str, int]:
        if not v:
            raise ValueError("At least one variant is required")
        if any(w < 0 for w in v.values()):
            raise ValueError("Variant weights must be non-negative")
        if sum(v.values()) != 100:
            raise ValueError(f"Variant weights must sum to 100, got {sum(v.values())}")
        return v


class ExperimentUpdate(BaseModel):
    """Request to update an experiment."""

    description: Optional[str] = Field(None, max_length=500)
    variants: Optional[Dict[str, int]] = None
    active: Optional[bool] = None

    @field_validator("variants")
    @classmethod
    def validate_variants(cls, v: Optional[Dict[str, int]]) -> Optional[Dict[str, int]]:
        if v is not None:
            if not v:
                raise ValueError("At least one variant is required")
            if any(w < 0 for w in v.values()):
                raise ValueError("Variant weights must be non-negative")
            if sum(v.values()) != 100:
                raise ValueError(f"Variant weights must sum to 100, got {sum(v.values())}")
        return v


class ExperimentResponse(BaseModel):
    """Experiment data returned to client."""

    id: UUID
    key: str
    description: Optional[str]
    variants: Dict[str, int]
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True
