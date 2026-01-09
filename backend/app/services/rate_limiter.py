"""Rate limiting service using Redis."""
import redis
from datetime import datetime
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

        Uses fixed window algorithm:
        - Window resets every `window` seconds
        - Allows up to `limit` requests per window

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
        # Create time-based key (resets each window)
        # Format: rate_limit:{key}:{YYYYMMDDHH} for hourly windows
        window_key = self._get_window_key(key, window)

        # Get current count
        current = self.redis.get(window_key)

        if current and int(current) >= limit:
            return False, int(current)

        # Increment counter atomically
        pipe = self.redis.pipeline()
        pipe.incr(window_key)
        pipe.expire(window_key, window)
        results = pipe.execute()

        new_count = results[0]
        return new_count <= limit, new_count

    def _get_window_key(self, key: str, window: int) -> str:
        """Generate Redis key for current time window."""
        now = datetime.utcnow()

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
        # Delete all keys matching pattern
        pattern = f"rate_limit:{key}:*"
        for redis_key in self.redis.scan_iter(match=pattern):
            self.redis.delete(redis_key)

    def get_remaining(self, key: str, limit: int = 100, window: int = 3600) -> int:
        """Get remaining requests in current window."""
        window_key = self._get_window_key(key, window)
        current = self.redis.get(window_key)
        used = int(current) if current else 0
        return max(0, limit - used)
