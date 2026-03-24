"""Tests for stream limiting service."""
import pytest
from unittest.mock import MagicMock
from app.services.stream_limiter import StreamLimiter, StreamLimitExceeded


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    redis_mock = MagicMock()
    redis_mock.scard.return_value = 0
    redis_mock.eval.return_value = 1  # Default: acquire succeeds
    return redis_mock


def test_try_acquire_stream_succeeds_under_limit(mock_redis):
    """Test that stream acquisition succeeds when under limit."""
    mock_redis.eval.return_value = 1
    limiter = StreamLimiter(mock_redis, default_limit=5)

    stream_id = limiter.try_acquire_stream("user_123")

    assert stream_id is not None
    assert len(stream_id) == 36  # UUID format


def test_try_acquire_stream_fails_at_limit(mock_redis):
    """Test that stream acquisition fails when at limit."""
    mock_redis.eval.return_value = 0
    limiter = StreamLimiter(mock_redis, default_limit=5)

    stream_id = limiter.try_acquire_stream("user_123")

    assert stream_id is None


def test_try_acquire_calls_lua_script(mock_redis):
    """Test that try_acquire_stream uses the atomic Lua script."""
    mock_redis.eval.return_value = 1
    limiter = StreamLimiter(mock_redis, default_limit=5)

    limiter.try_acquire_stream("user_123")

    mock_redis.eval.assert_called_once()
    args = mock_redis.eval.call_args
    # Lua script is first arg, 1 key, then key name, limit, stream_id, ttl
    assert args[0][1] == 1  # number of keys


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


def test_stream_context_acquires_and_unregisters(mock_redis):
    """Test that stream_context properly manages stream lifecycle."""
    mock_redis.eval.return_value = 1
    limiter = StreamLimiter(mock_redis, default_limit=5)

    with limiter.stream_context("user_123") as stream_id:
        assert stream_id is not None

    mock_redis.srem.assert_called_once()


def test_stream_context_raises_when_limit_exceeded(mock_redis):
    """Test that stream_context raises when limit is exceeded."""
    mock_redis.eval.return_value = 0
    limiter = StreamLimiter(mock_redis, default_limit=5)

    with pytest.raises(StreamLimitExceeded) as exc_info:
        with limiter.stream_context("user_123"):
            pass

    assert "Maximum concurrent streams" in str(exc_info.value)


def test_stream_context_unregisters_on_exception(mock_redis):
    """Test that stream_context unregisters even when exception occurs."""
    mock_redis.eval.return_value = 1
    limiter = StreamLimiter(mock_redis, default_limit=5)

    with pytest.raises(ValueError):
        with limiter.stream_context("user_123"):
            raise ValueError("Test error")

    # Should still unregister
    mock_redis.srem.assert_called_once()


def test_custom_limit_override(mock_redis):
    """Test that custom limits can override default."""
    # First call: limit=3, should fail
    mock_redis.eval.return_value = 0
    limiter = StreamLimiter(mock_redis, default_limit=5)

    assert limiter.try_acquire_stream("user_123", limit=3) is None

    # Second call: limit=10, should succeed
    mock_redis.eval.return_value = 1
    assert limiter.try_acquire_stream("user_123", limit=10) is not None
