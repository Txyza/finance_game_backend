"""Celery application instance and configuration."""

from __future__ import annotations

from typing import cast

from datetime import timedelta

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "finance_game",
    broker=cast(str, settings.REDIS_URL),
    backend=cast(str, settings.REDIS_URL),
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "daily-system-maintenance": {
            "task": "app.celery.tasks.daily.run_daily_maintenance",
            "schedule": crontab(hour=0, minute=0),
            "options": {"queue": "maintenance"},
        },
        "recover-inactive-users": {
            "task": "app.celery.tasks.energy.recover_inactive_users",
            "schedule": timedelta(minutes=20),
            "options": {"queue": "maintenance"},
        },
    },
)

celery_app.autodiscover_tasks(["app.celery.tasks"])

# Celery expects an attribute called ``app`` when autodiscovering via ``-A`` CLI flag.
app = celery_app

__all__ = ("celery_app",)
