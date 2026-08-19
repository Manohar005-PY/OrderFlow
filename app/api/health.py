import asyncio

import aio_pika
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from sqlalchemy import text

from app.core.config import settings
from app.db.session import SessionLocal


router = APIRouter(tags=["Health"])


@router.get("/health/live")
def liveness():
    return {"status": "ok"}


@router.get("/health/ready")
async def readiness():
    checks: dict[str, str] = {}

    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "down"
    finally:
        db.close()

    redis = Redis.from_url(settings.REDIS_URL)
    try:
        await asyncio.wait_for(redis.ping(), timeout=2)
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "down"
    finally:
        await redis.aclose()

    connection = None
    try:
        connection = await asyncio.wait_for(
            aio_pika.connect_robust(settings.RABBITMQ_URL),
            timeout=2,
        )
        checks["rabbitmq"] = "ok"
    except Exception:
        checks["rabbitmq"] = "down"
    finally:
        if connection:
            await connection.close()

    healthy = all(value == "ok" for value in checks.values())
    return JSONResponse(
        status_code=(
            status.HTTP_200_OK
            if healthy
            else status.HTTP_503_SERVICE_UNAVAILABLE
        ),
        content={"status": "ok" if healthy else "degraded", "checks": checks},
    )
