"""Health check endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import redis

from app.database import get_db
from app.config import get_settings

router = APIRouter()
settings = get_settings()


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
        "redis": "unknown"
    }

    # Check database
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {str(e)}"

    # Check Redis
    try:
        redis_client = redis.from_url(settings.redis_url)
        redis_client.ping()
        checks["redis"] = "healthy"
    except Exception as e:
        checks["redis"] = f"unhealthy: {str(e)}"

    # Overall status
    overall_status = "healthy" if all(
        v == "healthy" for v in checks.values()
    ) else "degraded"

    return {
        "status": overall_status,
        "checks": checks
    }
