import logging
from datetime import datetime, timezone

from app.celery import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.celery.tasks.daily.run_daily_maintenance")
def run_daily_maintenance() -> str:
    """Example periodic task executed once per day."""

    timestamp = datetime.now(timezone.utc).isoformat()
    message = f"Daily maintenance completed at {timestamp}"
    logger.info(message)
    return message
