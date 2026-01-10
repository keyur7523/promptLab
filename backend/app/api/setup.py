"""Setup endpoint for database initialization."""
from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal, engine, Base
from app.models import User, Experiment
from app.middleware.auth import hash_api_key

router = APIRouter()


@router.post("/setup/init-db")
async def initialize_database():
    """
    Initialize database tables and create initial data.

    This endpoint should only be called once after deployment.
    Creates tables, test user, and sample experiment.
    """
    db: Session = SessionLocal()

    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)

        # Check if already initialized
        existing_user = db.query(User).first()
        if existing_user:
            return {
                "status": "already_initialized",
                "message": "Database already has data. Skipping initialization."
            }

        # Create test user with API key
        test_api_key = "test-key-123"

        try:
            api_key_hash = hash_api_key(test_api_key)
        except Exception as e:
            # Fallback to SHA256 if bcrypt fails
            import hashlib
            api_key_hash = hashlib.sha256(test_api_key.encode()).hexdigest()

        user = User(
            api_key_hash=api_key_hash,
            rate_limit=100
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create sample experiment
        experiment = Experiment(
            key="prompt_experiment_jan2024",
            description="Test concise vs detailed prompts",
            variants={
                "control": 34,
                "concise": 33,
                "friendly": 33
            },
            active=True
        )
        db.add(experiment)
        db.commit()

        return {
            "status": "success",
            "message": "Database initialized successfully",
            "user_id": str(user.id),
            "api_key": test_api_key,
            "experiment": experiment.key,
            "note": "Save your API key! This is the only time it will be shown."
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database initialization failed: {str(e)}"
        )
    finally:
        db.close()
