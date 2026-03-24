"""Experiment CRUD endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_db
from app.models.user import User
from app.models.experiment import Experiment
from app.schemas.experiment import ExperimentCreate, ExperimentUpdate, ExperimentResponse
from app.services.experiments import ExperimentService
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.get("", response_model=List[ExperimentResponse])
async def list_experiments(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all experiments (active and inactive), ordered by creation date."""
    experiments = (
        db.query(Experiment)
        .order_by(Experiment.created_at.desc())
        .all()
    )
    return experiments


@router.post("", response_model=ExperimentResponse, status_code=201)
async def create_experiment(
    data: ExperimentCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new experiment. Variant weights must sum to 100."""
    # Check for duplicate key
    existing = db.query(Experiment).filter(Experiment.key == data.key).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Experiment with key '{data.key}' already exists")

    service = ExperimentService(db)
    experiment = service.create_experiment(
        key=data.key,
        description=data.description,
        variants=data.variants,
    )
    return experiment


@router.patch("/{experiment_id}", response_model=ExperimentResponse)
async def update_experiment(
    experiment_id: UUID,
    data: ExperimentUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update an experiment's description, variants, or active status."""
    experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    if data.description is not None:
        experiment.description = data.description
    if data.variants is not None:
        experiment.variants = data.variants
    if data.active is not None:
        experiment.active = data.active

    db.commit()
    db.refresh(experiment)
    return experiment


@router.delete("/{experiment_id}", status_code=204)
async def delete_experiment(
    experiment_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete an experiment."""
    experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    db.delete(experiment)
    db.commit()
