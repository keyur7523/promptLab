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

        # IMPORTANT: Sort variants by key to ensure consistent ordering
        # PostgreSQL JSONB does NOT preserve insertion order, so we must sort
        # to guarantee deterministic assignment across all environments
        sorted_variants = sorted(experiment.variants.items(), key=lambda x: x[0])

        # Distribute users based on variant weights
        # Example: [("control", 50), ("variant_a", 30), ("variant_b", 20)]
        cumulative = 0
        for variant, weight in sorted_variants:
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

    def get_default_active_experiment(self) -> Optional[Experiment]:
        """
        Get the default active experiment for chat.

        Returns the first active experiment ordered by creation date.
        Used when no specific experiment key is configured.
        """
        return self.db.query(Experiment).filter(
            Experiment.active == True
        ).order_by(Experiment.created_at.asc()).first()

    def get_experiment_key_for_chat(self, configured_key: str = "") -> Optional[str]:
        """
        Get the experiment key to use for chat.

        Args:
            configured_key: Key from config/environment. If empty, auto-selects.

        Returns:
            Experiment key to use, or None if no active experiments.
        """
        if configured_key:
            # Use configured key if the experiment exists and is active
            experiment = self.get_active_experiment(configured_key)
            if experiment:
                return configured_key
            # Fall through to auto-select if configured experiment not found/active

        # Auto-select: get first active experiment
        experiment = self.get_default_active_experiment()
        return experiment.key if experiment else None

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
