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
        "daily-financial-events": {
            "task": "app.celery.tasks.financial_events.run_daily_financial_events",
            "schedule": crontab(hour=0, minute=0),
            "options": {"queue": "financial"},
        },
        "weekly-key-rate-update": {
            "task": "app.celery.tasks.financial_events.update_key_rate",
            "schedule": crontab(day_of_week="mon", hour=0, minute=0),
            "options": {"queue": "financial"},
        },
        "check-expired-deposits": {
            "task": "app.celery.tasks.financial_events.process_expired_deposits",
            "schedule": crontab(minute=0),  # Каждый час
            "options": {"queue": "financial"},
        },
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
        "cleanup-expired-user-items": {
            "task": "app.celery.tasks.inventory.cleanup_expired_user_items",
            "schedule": crontab(minute=5),
            "options": {"queue": "maintenance"},
        },
        "index-work-max-amount-yearly": {
            "task": "app.celery.tasks.financial_events.index_work_max_amount_yearly",
            "schedule": timedelta(days=28),
            "options": {"queue": "financial"},
        },
    },
)

celery_app.autodiscover_tasks(["app.celery.tasks"])

# Celery expects an attribute called ``app`` when autodiscovering via ``-A`` CLI flag.
app = celery_app

__all__ = ("celery_app",)
