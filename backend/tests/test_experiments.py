"""Tests for experimentation service."""
import pytest
from sqlalchemy.orm import Session

from app.models.experiment import Experiment
from app.services.experiments import ExperimentService


def test_deterministic_variant_assignment(db: Session):
    """Test that variant assignment is deterministic."""
    # Create test experiment
    experiment = Experiment(
        key="test_exp",
        description="Test experiment",
        variants={"control": 50, "variant_a": 50},
        active=True
    )
    db.add(experiment)
    db.commit()

    service = ExperimentService(db)

    # Same user should always get same variant
    variant1 = service.assign_variant("user_123", "test_exp")
    variant2 = service.assign_variant("user_123", "test_exp")
    variant3 = service.assign_variant("user_123", "test_exp")

    assert variant1 == variant2 == variant3, "Variant assignment should be deterministic"


def test_variant_distribution(db: Session):
    """Test that variants are distributed according to weights."""
    # Create experiment with known distribution
    experiment = Experiment(
        key="test_dist",
        description="Test distribution",
        variants={"control": 50, "variant_a": 50},
        active=True
    )
    db.add(experiment)
    db.commit()

    service = ExperimentService(db)

    # Assign variants to many users
    assignments = {}
    for i in range(1000):
        variant = service.assign_variant(f"user_{i}", "test_dist")
        assignments[variant] = assignments.get(variant, 0) + 1

    # Check that distribution is roughly 50/50 (allow 10% margin)
    control_pct = assignments.get("control", 0) / 1000 * 100
    assert 40 <= control_pct <= 60, f"Control should be ~50%, got {control_pct}%"


def test_inactive_experiment_returns_control(db: Session):
    """Test that inactive experiments return control variant."""
    # Create inactive experiment
    experiment = Experiment(
        key="test_inactive",
        description="Inactive test",
        variants={"control": 50, "variant_a": 50},
        active=False
    )
    db.add(experiment)
    db.commit()

    service = ExperimentService(db)
    variant = service.assign_variant("user_123", "test_inactive")

    assert variant == "control", "Inactive experiment should return control"


def test_nonexistent_experiment_returns_control(db: Session):
    """Test that nonexistent experiments return control variant."""
    service = ExperimentService(db)
    variant = service.assign_variant("user_123", "nonexistent_exp")

    assert variant == "control", "Nonexistent experiment should return control"


@pytest.fixture
def db():
    """Create test database session."""
    from app.database import SessionLocal, engine, Base

    # Create tables
    Base.metadata.create_all(bind=engine)

    # Create session
    session = SessionLocal()

    yield session

    # Cleanup
    session.close()
    Base.metadata.drop_all(bind=engine)
