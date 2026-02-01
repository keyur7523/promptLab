"""Tests for API key authentication."""
import pytest
from sqlalchemy.orm import Session

from app.models.user import User
from app.middleware.auth import hash_api_key, create_user_with_api_key


def test_hash_api_key_is_deterministic():
    """Test that hash_api_key produces consistent results."""
    api_key = "test-key-12345"

    hash1 = hash_api_key(api_key)
    hash2 = hash_api_key(api_key)
    hash3 = hash_api_key(api_key)

    assert hash1 == hash2 == hash3, "Hash should be deterministic"


def test_hash_api_key_is_sha256():
    """Test that hash_api_key uses SHA256."""
    import hashlib

    api_key = "test-key-12345"
    expected = hashlib.sha256(api_key.encode()).hexdigest()
    actual = hash_api_key(api_key)

    assert actual == expected, "Should use SHA256 hashing"
    assert len(actual) == 64, "SHA256 hex digest should be 64 characters"


def test_different_keys_produce_different_hashes():
    """Test that different API keys produce different hashes."""
    hash1 = hash_api_key("key-one")
    hash2 = hash_api_key("key-two")

    assert hash1 != hash2, "Different keys should produce different hashes"


def test_create_user_with_api_key(db: Session):
    """Test creating a user with an API key."""
    api_key = "new-test-key-abc123"

    user = create_user_with_api_key(db, api_key, rate_limit=50)

    assert user.id is not None
    assert user.api_key_hash == hash_api_key(api_key)
    assert user.rate_limit == 50


def test_user_lookup_by_hash(db: Session):
    """Test that users can be looked up directly by hash."""
    api_key = "lookup-test-key"
    expected_hash = hash_api_key(api_key)

    # Create user
    user = User(api_key_hash=expected_hash, rate_limit=100)
    db.add(user)
    db.commit()

    # Lookup by hash (this is how get_current_user works)
    found_user = db.query(User).filter(
        User.api_key_hash == expected_hash
    ).first()

    assert found_user is not None
    assert found_user.id == user.id


def test_invalid_hash_returns_none(db: Session):
    """Test that invalid hash returns no user."""
    # Create a user with one key
    user = User(api_key_hash=hash_api_key("real-key"), rate_limit=100)
    db.add(user)
    db.commit()

    # Try to find with wrong key
    wrong_hash = hash_api_key("wrong-key")
    found_user = db.query(User).filter(
        User.api_key_hash == wrong_hash
    ).first()

    assert found_user is None


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
