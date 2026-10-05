"""Health check and readiness probe endpoints."""
import time

from fastapi import APIRouter
from starlette.responses import JSONResponse
from sqlalchemy import text

from src.observability.logging import get_logger

health_router = APIRouter(tags=["health"])
log = get_logger("health")


@health_router.get("/health")
async def liveness():
    """Liveness probe — confirms the process is running."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
    }


@health_router.get("/ready")
async def readiness():
    """Readiness probe — confirms dependencies are reachable."""
    checks = {}
    overall = "ready"

    # Database check
    try:
        from src.database import engine
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = {"status": "healthy"}
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "error": str(e)}
        overall = "not_ready"

    # Redis check
    try:
        import redis.asyncio as aioredis
        from src.config import settings
        r = aioredis.from_url(settings.redis_url, socket_timeout=2)
        await r.ping()
        await r.aclose()
        checks["redis"] = {"status": "healthy"}
    except Exception as e:
        checks["redis"] = {"status": "unhealthy", "error": str(e)}
        overall = "not_ready"

    status_code = 200 if overall == "ready" else 503

    log.info("readiness_check", status=overall, checks=checks)

    return JSONResponse(
        content={
            "status": overall,
            "timestamp": time.time(),
            "checks": checks,
        },
        status_code=status_code,
    )
