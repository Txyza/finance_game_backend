import logging
from datetime import datetime, timezone

from app.celery import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.celery.tasks.monitoring.check_service_health")
def check_service_health() -> dict[str, str]:
    """Simple task to confirm the worker is alive."""

    result = {
        "status": "ok",
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }
    logger.info("Health check executed", extra=result)
    return result
