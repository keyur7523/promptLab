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

    def can_start_stream(self, user_id: str, limit: Optional[int] = None) -> bool:
        """Check if user can start a new stream."""
        max_streams = limit or self.default_limit
        current = self.get_active_stream_count(user_id)
        return current < max_streams

    def register_stream(self, user_id: str) -> str:
        """
        Register a new stream for a user.

        Returns:
            Unique stream ID to use for cleanup
        """
        stream_id = str(uuid.uuid4())
        key = self._get_streams_key(user_id)

        pipe = self.redis.pipeline()
        pipe.sadd(key, stream_id)
        pipe.expire(key, self.stream_ttl)
        pipe.execute()

        return stream_id

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
        max_streams = limit or self.default_limit

        if not self.can_start_stream(user_id, max_streams):
            raise StreamLimitExceeded(
                f"Maximum concurrent streams ({max_streams}) exceeded"
            )

        stream_id = self.register_stream(user_id)
        try:
            yield stream_id
        finally:
            self.unregister_stream(user_id, stream_id)


class StreamLimitExceeded(Exception):
    """Raised when a user exceeds their concurrent stream limit."""
    pass
