"""Setup endpoint for database initialization."""
import secrets
import logging

from fastapi import APIRouter, HTTPException, Header
from typing import Optional

from app.database import SessionLocal
from app.models import User, Experiment
from app.middleware.auth import hash_api_key
from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.post("/setup/init-db")
async def initialize_database(
    x_bootstrap_token: Optional[str] = Header(None),
):
    """
    Initialize database and seed initial data.

    Requires tables to already exist (run `alembic upgrade head` first).
    Protected by BOOTSTRAP_TOKEN env var — if set, the request must include
    the matching X-Bootstrap-Token header.

    Only callable when the database is empty (no existing users).
    """
    # Verify bootstrap token if configured
    if settings.bootstrap_token:
        if not x_bootstrap_token or x_bootstrap_token != settings.bootstrap_token:
            raise HTTPException(status_code=403, detail="Invalid bootstrap token.")

    db = SessionLocal()

    try:
        # Tables must already exist via Alembic — don't create_all here
        existing_user = db.query(User).first()
        if existing_user:
            raise HTTPException(
                status_code=409,
                detail="Database already initialized."
            )

        # Generate a secure random API key
        generated_api_key = f"pk-{secrets.token_urlsafe(32)}"
        api_key_hash = hash_api_key(generated_api_key)

        user = User(
            api_key_hash=api_key_hash,
            rate_limit=100
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create sample experiment
        experiment = Experiment(
            key="prompt_experiment_v1",
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
            "api_key": generated_api_key,
            "experiment": experiment.key,
            "note": "Save your API key! This is the only time it will be shown."
        }

    except HTTPException:
        raise
    except Exception:
        db.rollback()
        logging.exception("Database initialization failed")
        raise HTTPException(
            status_code=500,
            detail="Database initialization failed. Check server logs for details."
        )
    finally:
        db.close()
