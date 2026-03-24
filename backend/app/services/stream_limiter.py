"""Stream limiting service for backpressure control.

Limits concurrent SSE streams per user to prevent resource exhaustion.
Uses Redis for distributed tracking across multiple workers.
"""
import redis
from typing import Optional
from contextlib import contextmanager
import uuid


class StreamLimiter:
    """Redis-based concurrent stream limiter."""

    def __init__(self, redis_client: redis.Redis, default_limit: int = 5):
        self.redis = redis_client
        self.default_limit = default_limit
        # Stream keys expire after 5 minutes (safety net for cleanup failures)
        self.stream_ttl = 300

    def _get_streams_key(self, user_id: str) -> str:
        """Get Redis key for user's active streams set."""
        return f"streams:active:{user_id}"

    def get_active_stream_count(self, user_id: str) -> int:
        """Get count of active streams for a user."""
        key = self._get_streams_key(user_id)
        return self.redis.scard(key) or 0

    def try_acquire_stream(self, user_id: str, limit: Optional[int] = None) -> Optional[str]:
        """
        Atomically check limit and register a stream using a Lua script.

        Returns:
            Stream ID if acquired, None if limit exceeded.
        """
        max_streams = limit or self.default_limit
        key = self._get_streams_key(user_id)
        stream_id = str(uuid.uuid4())

        # Lua script: atomic check-and-add to avoid TOCTOU race
        lua_script = """
        local current = redis.call('SCARD', KEYS[1])
        if current >= tonumber(ARGV[1]) then
            return 0
        end
        redis.call('SADD', KEYS[1], ARGV[2])
        redis.call('EXPIRE', KEYS[1], ARGV[3])
        return 1
        """
        acquired = self.redis.eval(lua_script, 1, key, max_streams, stream_id, self.stream_ttl)

        if acquired == 1:
            return stream_id
        return None

    def unregister_stream(self, user_id: str, stream_id: str) -> None:
        """Remove a stream from the active set."""
        key = self._get_streams_key(user_id)
        self.redis.srem(key, stream_id)

    @contextmanager
    def stream_context(self, user_id: str, limit: Optional[int] = None):
        """
        Context manager for stream lifecycle.

        Usage:
            with stream_limiter.stream_context(user_id) as stream_id:
                # Stream is registered
                async for token in stream_response():
                    yield token
            # Stream is automatically unregistered

        Raises:
            StreamLimitExceeded: If user has too many concurrent streams
        """
        stream_id = self.try_acquire_stream(user_id, limit)

        if stream_id is None:
            max_streams = limit or self.default_limit
            raise StreamLimitExceeded(
                f"Maximum concurrent streams ({max_streams}) exceeded"
            )

        try:
            yield stream_id
        finally:
            self.unregister_stream(user_id, stream_id)


class StreamLimitExceeded(Exception):
    """Raised when a user exceeds their concurrent stream limit."""
    pass
