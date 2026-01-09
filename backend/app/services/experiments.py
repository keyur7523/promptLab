"""Experimentation service for A/B testing."""
import hashlib
from typing import Dict, Optional
from sqlalchemy.orm import Session

from app.models.experiment import Experiment


class ExperimentService:
    """Service for managing A/B experiments."""

    def __init__(self, db: Session):
        self.db = db

    def assign_variant(self, user_id: str, experiment_key: str) -> str:
        """
        Deterministically assign a variant to a user for a given experiment.

        Uses consistent hashing to ensure the same user always gets the same variant.

        Args:
            user_id: Unique user identifier
            experiment_key: Experiment identifier

        Returns:
            Variant name (e.g., "control", "variant_a")

        Example:
            >>> service = ExperimentService(db)
            >>> variant = service.assign_variant("user_123", "prompt_exp_jan2024")
            >>> print(variant)  # "control" or "variant_a" deterministically
        """
        # Get experiment config from database
        experiment = self.db.query(Experiment).filter(
            Experiment.key == experiment_key,
            Experiment.active == True
        ).first()

        if not experiment:
            return "control"  # Default to control if experiment not found

        # Create deterministic hash from user_id + experiment_key
        hash_input = f"{user_id}{experiment_key}".encode('utf-8')
        hash_digest = hashlib.sha256(hash_input).hexdigest()
        hash_value = int(hash_digest[:8], 16) % 100  # Take first 8 chars, convert to 0-99

        # Distribute users based on variant weights
        # Example: {"control": 50, "variant_a": 30, "variant_b": 20}
        cumulative = 0
        for variant, weight in experiment.variants.items():
            cumulative += weight
            if hash_value < cumulative:
                return variant

        # Fallback to control (should never reach here if weights sum to 100)
        return "control"

    def get_active_experiment(self, key: str) -> Optional[Experiment]:
        """Get active experiment by key."""
        return self.db.query(Experiment).filter(
            Experiment.key == key,
            Experiment.active == True
        ).first()

    def create_experiment(
        self,
        key: str,
        description: str,
        variants: Dict[str, int]
    ) -> Experiment:
        """
        Create a new experiment.

        Args:
            key: Unique experiment identifier
            description: Human-readable description
            variants: Dict mapping variant names to weights (must sum to 100)

        Returns:
            Created Experiment instance

        Raises:
            ValueError: If variant weights don't sum to 100
        """
        if sum(variants.values()) != 100:
            raise ValueError("Variant weights must sum to 100")

        experiment = Experiment(
            key=key,
            description=description,
            variants=variants,
            active=True
        )
        self.db.add(experiment)
        self.db.commit()
        self.db.refresh(experiment)
        return experiment
