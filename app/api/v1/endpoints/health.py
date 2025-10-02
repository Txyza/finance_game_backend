from datetime import datetime, UTC
from typing import Dict, Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.db.database import get_session
from app.celery.tasks.monitoring import check_service_health

router = APIRouter(tags=["health"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check(db: AsyncSession = Depends(get_session)) -> Dict[str, Any]:
    """
    Health check endpoint
    """
    try:
        # Check database connection
        result = await db.execute(text("SELECT 1"))
        db_status = "ok" if result else "error"
    except Exception:
        db_status = "error"

    celery_result = check_service_health.delay()

    return {
        "status": "ok",
        "timestamp": datetime.now(UTC).isoformat(),
        "service": "finance-game-api",
        "version": "1.0.0",
        "database": db_status,
        "celery": {
            "task_id": celery_result.id,
            "state": celery_result.state,
        },
    }
