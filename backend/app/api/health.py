"""Health check endpoints."""
import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import redis

from app.database import get_db
from app.config import get_settings

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)

# Shared Redis client for health checks
_redis_client: redis.Redis | None = None


def _get_redis_client() -> redis.Redis | None:
    """Get or create a shared Redis client for health checks."""
    global _redis_client
    if _redis_client is None and settings.redis_url:
        try:
            _redis_client = redis.from_url(settings.redis_url)
        except Exception:
            pass
    return _redis_client


@router.get("/health")
@router.head("/health")
async def health_check():
    """Basic health check."""
    return {"status": "healthy", "service": "promptlab-backend"}


@router.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """
    Detailed health check including database and Redis connectivity.
    """
    checks = {
        "api": "healthy",
        "database": "unknown",
        "redis": "not configured" if not settings.redis_url else "unknown",
    }

    # Check database
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "healthy"
    except Exception as e:
        logger.warning("Health check: database unhealthy: %s", e)
        checks["database"] = "unhealthy"

    # Check Redis (optional)
    client = _get_redis_client()
    if client:
        try:
            client.ping()
            checks["redis"] = "healthy"
        except Exception as e:
            logger.warning("Health check: redis unhealthy: %s", e)
            checks["redis"] = "unhealthy"

    # Overall status
    overall_status = "healthy" if all(
        v in ("healthy", "not configured") for v in checks.values()
    ) else "degraded"

    return {
        "status": overall_status,
        "checks": checks
    }
