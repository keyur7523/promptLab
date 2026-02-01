"""Initialize database with sample data."""
import sys
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
            print("✓ Database already initialized")
            return

        # Create test user with API key
        test_api_key = "test-key-123"  # Shorter key for testing
        print(f"\nCreating test user with API key: {test_api_key}")

        # Hash using SHA256 (deterministic, allows direct DB lookup)
        api_key_hash = hash_api_key(test_api_key)

        user = User(
            api_key_hash=api_key_hash,
            rate_limit=100
        )
        db.add(user)
        db.commit()
        print(f"✓ Created user with ID: {user.id}")

        # Create sample experiment
        print("\nCreating sample experiment...")
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
        print(f"✓ Created experiment: {experiment.key}")

        print("\n" + "="*50)
        print("✓ Database initialized successfully!")
        print("="*50)
        print(f"\nTest API Key: {test_api_key}")
        print("Use this key in the frontend or with curl:")
        print(f'  curl -H "x-api-key: {test_api_key}" http://localhost:8000/health')
        print("\n" + "="*50)

    except Exception as e:
        print(f"✗ Error initializing database: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    init_database()
