"""Rate limiting service using Redis."""
import redis
from datetime import datetime, timezone
from typing import Tuple


class RateLimiter:
    """Redis-based fixed window rate limiter."""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    def check_rate_limit(
        self,
        key: str,
        limit: int = 100,
        window: int = 3600
    ) -> Tuple[bool, int]:
        """
        Check if request is within rate limit.

        Uses fixed window algorithm with atomic INCR-first to avoid TOCTOU races:
        - Increment first, then check the returned value
        - If over limit, the count is slightly inflated but never under-counted

        Args:
            key: Unique identifier (e.g., API key or user ID)
            limit: Maximum requests allowed per window
            window: Time window in seconds (default: 3600 = 1 hour)

        Returns:
            Tuple of (allowed: bool, current_count: int)

        Example:
            >>> limiter = RateLimiter(redis_client)
            >>> allowed, count = limiter.check_rate_limit("user_123", limit=100, window=3600)
            >>> if not allowed:
            >>>     raise HTTPException(429, "Rate limit exceeded")
        """
        window_key = self._get_window_key(key, window)

        # Atomic increment-first: avoids TOCTOU race between GET and INCR
        pipe = self.redis.pipeline()
        pipe.incr(window_key)
        pipe.expire(window_key, window)
        results = pipe.execute()

        current_count = results[0]
        return current_count <= limit, current_count

    def _get_window_key(self, key: str, window: int) -> str:
        """Generate Redis key for current time window."""
        now = datetime.now(timezone.utc)

        if window == 3600:  # 1 hour
            window_id = now.strftime('%Y%m%d%H')
        elif window == 60:  # 1 minute
            window_id = now.strftime('%Y%m%d%H%M')
        elif window == 86400:  # 1 day
            window_id = now.strftime('%Y%m%d')
        else:
            # For custom windows, use timestamp divided by window
            window_id = str(int(now.timestamp()) // window)

        return f"rate_limit:{key}:{window_id}"

    def reset(self, key: str):
        """Reset rate limit for a key (useful for testing)."""
        pattern = f"rate_limit:{key}:*"
        for redis_key in self.redis.scan_iter(match=pattern):
            self.redis.delete(redis_key)

    def get_remaining(self, key: str, limit: int = 100, window: int = 3600) -> int:
        """Get remaining requests in current window."""
        window_key = self._get_window_key(key, window)
        current = self.redis.get(window_key)
        used = int(current) if current else 0
        return max(0, limit - used)
