"""Initialize database with sample data."""
import sys
import secrets
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models import User, Experiment
from app.middleware.auth import hash_api_key


def init_database():
    """Initialize database with sample user and experiment."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()

    try:
        # Check if user already exists
        existing_user = db.query(User).first()
        if existing_user:
            print("Database already initialized")
            return

        # Generate a secure random API key
        api_key = f"pk-{secrets.token_urlsafe(32)}"
        api_key_hash = hash_api_key(api_key)

        user = User(
            api_key_hash=api_key_hash,
            rate_limit=100
        )
        db.add(user)
        db.commit()
        print(f"Created user with ID: {user.id}")

        # Create sample experiment
        print("Creating sample experiment...")
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
        print(f"Created experiment: {experiment.key}")

        print()
        print("=" * 50)
        print("Database initialized successfully!")
        print("=" * 50)
        print()
        print(f"API Key: {api_key}")
        print("Save this key! It will not be shown again.")
        print()
        print("Use this key in the frontend .env:")
        print(f"  VITE_API_KEY={api_key}")
        print()
        print("Or with curl:")
        print(f'  curl -H "x-api-key: {api_key}" http://localhost:8000/health')
        print("=" * 50)

    except Exception as e:
        print(f"Error initializing database: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    init_database()
