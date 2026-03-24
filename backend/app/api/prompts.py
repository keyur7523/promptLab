"""Prompt version registry endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from uuid import UUID

from app.database import get_db
from app.models.user import User
from app.models.prompt_version import PromptVersion
from app.schemas.prompt import PromptCreate, PromptResponse
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/prompts", tags=["prompts"])


@router.get("", response_model=List[PromptResponse])
async def list_prompts(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all prompt versions, newest first."""
    return (
        db.query(PromptVersion)
        .order_by(PromptVersion.variant, PromptVersion.version.desc())
        .all()
    )


@router.get("/{variant}", response_model=List[PromptResponse])
async def get_variant_history(
    variant: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get version history for a specific variant, newest first."""
    versions = (
        db.query(PromptVersion)
        .filter(PromptVersion.variant == variant)
        .order_by(PromptVersion.version.desc())
        .all()
    )
    if not versions:
        raise HTTPException(status_code=404, detail=f"No prompts found for variant '{variant}'")
    return versions


@router.post("", response_model=PromptResponse, status_code=201)
async def create_prompt_version(
    data: PromptCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new prompt version for a variant.

    Auto-increments the version number and sets it as active.
    Previous active version for this variant is deactivated.
    """
    # Get next version number for this variant
    max_version = (
        db.query(func.max(PromptVersion.version))
        .filter(PromptVersion.variant == data.variant)
        .scalar()
    )
    next_version = (max_version or 0) + 1

    # Deactivate current active version for this variant
    db.query(PromptVersion).filter(
        PromptVersion.variant == data.variant,
        PromptVersion.is_active == True,
    ).update({"is_active": False})

    # Create new version
    prompt = PromptVersion(
        variant=data.variant,
        version=next_version,
        content=data.content,
        is_active=True,
    )
    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    return prompt


@router.patch("/{prompt_id}/activate", response_model=PromptResponse)
async def activate_prompt_version(
    prompt_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Activate a specific prompt version (rollback).

    Deactivates all other versions for the same variant.
    """
    prompt = db.query(PromptVersion).filter(PromptVersion.id == prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt version not found")

    # Deactivate all versions for this variant
    db.query(PromptVersion).filter(
        PromptVersion.variant == prompt.variant,
        PromptVersion.is_active == True,
    ).update({"is_active": False})

    # Activate the selected version
    prompt.is_active = True
    db.commit()
    db.refresh(prompt)
    return prompt
