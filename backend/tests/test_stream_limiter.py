"""Tests for stream limiting service."""
import pytest
from unittest.mock import MagicMock, patch
from app.services.stream_limiter import StreamLimiter, StreamLimitExceeded


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    redis_mock = MagicMock()
    redis_mock.scard.return_value = 0
    redis_mock.pipeline.return_value = MagicMock()
    return redis_mock


def test_can_start_stream_when_under_limit(mock_redis):
    """Test that streams can start when under limit."""
    mock_redis.scard.return_value = 2
    limiter = StreamLimiter(mock_redis, default_limit=5)

    assert limiter.can_start_stream("user_123") is True


def test_cannot_start_stream_when_at_limit(mock_redis):
    """Test that streams cannot start when at limit."""
    mock_redis.scard.return_value = 5
    limiter = StreamLimiter(mock_redis, default_limit=5)

    assert limiter.can_start_stream("user_123") is False


def test_cannot_start_stream_when_over_limit(mock_redis):
    """Test that streams cannot start when over limit."""
    mock_redis.scard.return_value = 10
    limiter = StreamLimiter(mock_redis, default_limit=5)

    assert limiter.can_start_stream("user_123") is False


def test_register_stream_returns_unique_id(mock_redis):
    """Test that register_stream returns a unique stream ID."""
    pipe_mock = MagicMock()
    mock_redis.pipeline.return_value = pipe_mock

    limiter = StreamLimiter(mock_redis, default_limit=5)
    stream_id = limiter.register_stream("user_123")

    assert stream_id is not None
    assert len(stream_id) == 36  # UUID format


def test_register_stream_adds_to_redis(mock_redis):
    """Test that register_stream adds the stream to Redis."""
    pipe_mock = MagicMock()
    mock_redis.pipeline.return_value = pipe_mock

    limiter = StreamLimiter(mock_redis, default_limit=5)
    stream_id = limiter.register_stream("user_123")

    pipe_mock.sadd.assert_called_once()
    pipe_mock.expire.assert_called_once()
    pipe_mock.execute.assert_called_once()


def test_unregister_stream_removes_from_redis(mock_redis):
    """Test that unregister_stream removes the stream from Redis."""
    limiter = StreamLimiter(mock_redis, default_limit=5)
    limiter.unregister_stream("user_123", "stream-id-abc")

    mock_redis.srem.assert_called_once()


def test_get_active_stream_count(mock_redis):
    """Test getting active stream count."""
    mock_redis.scard.return_value = 3
    limiter = StreamLimiter(mock_redis, default_limit=5)

    count = limiter.get_active_stream_count("user_123")

    assert count == 3


def test_stream_context_registers_and_unregisters(mock_redis):
    """Test that stream_context properly manages stream lifecycle."""
    pipe_mock = MagicMock()
    mock_redis.pipeline.return_value = pipe_mock
    mock_redis.scard.return_value = 0

    limiter = StreamLimiter(mock_redis, default_limit=5)

    with limiter.stream_context("user_123") as stream_id:
        assert stream_id is not None
        pipe_mock.sadd.assert_called_once()

    mock_redis.srem.assert_called_once()


def test_stream_context_raises_when_limit_exceeded(mock_redis):
    """Test that stream_context raises when limit is exceeded."""
    mock_redis.scard.return_value = 5
    limiter = StreamLimiter(mock_redis, default_limit=5)

    with pytest.raises(StreamLimitExceeded) as exc_info:
        with limiter.stream_context("user_123"):
            pass

    assert "Maximum concurrent streams" in str(exc_info.value)


def test_stream_context_unregisters_on_exception(mock_redis):
    """Test that stream_context unregisters even when exception occurs."""
    pipe_mock = MagicMock()
    mock_redis.pipeline.return_value = pipe_mock
    mock_redis.scard.return_value = 0

    limiter = StreamLimiter(mock_redis, default_limit=5)

    with pytest.raises(ValueError):
        with limiter.stream_context("user_123"):
            raise ValueError("Test error")

    # Should still unregister
    mock_redis.srem.assert_called_once()


def test_custom_limit_override(mock_redis):
    """Test that custom limits can override default."""
    mock_redis.scard.return_value = 3
    limiter = StreamLimiter(mock_redis, default_limit=5)

    # Should fail with custom limit of 3
    assert limiter.can_start_stream("user_123", limit=3) is False

    # Should pass with custom limit of 10
    assert limiter.can_start_stream("user_123", limit=10) is True
