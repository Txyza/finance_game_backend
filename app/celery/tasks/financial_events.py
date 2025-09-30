"""
Celery задачи для финансовых игровых событий
"""

import logging
from datetime import datetime, timezone

from app.celery import celery_app
from app.db.database import async_session_maker
from app.services.daily_events import DailyEventsService

logger = logging.getLogger(__name__)


@celery_app.task(name="app.celery.tasks.financial_events.process_savings_interest")
def process_savings_interest() -> str:
    """
    Начисление процентов по накопительным счетам
    """
    import asyncio

    async def _process():
        service = DailyEventsService(async_session_maker)
        await service.process_savings_interest()
        return "Savings interest processed successfully"

    try:
        result = asyncio.run(_process())
        logger.info("Savings interest processing completed")
        return result
    except Exception as e:
        logger.error(f"Error processing savings interest: {e}")
        raise


@celery_app.task(name="app.celery.tasks.financial_events.process_deposits_interest")
def process_deposits_interest() -> str:
    """
    Начисление процентов по вкладам
    """
    import asyncio

    async def _process():
        service = DailyEventsService(async_session_maker)
        await service.process_deposits_interest()
        return "Deposits interest processed successfully"

    try:
        result = asyncio.run(_process())
        logger.info("Deposits interest processing completed")
        return result
    except Exception as e:
        logger.error(f"Error processing deposits interest: {e}")
        raise


@celery_app.task(name="app.celery.tasks.financial_events.process_expired_deposits")
def process_expired_deposits() -> str:
    """
    Автоматическое закрытие истекших вкладов
    """
    import asyncio

    async def _process():
        service = DailyEventsService(async_session_maker)
        await service.process_expired_deposits()
        return "Expired deposits processed successfully"

    try:
        result = asyncio.run(_process())
        logger.info("Expired deposits processing completed")
        return result
    except Exception as e:
        logger.error(f"Error processing expired deposits: {e}")
        raise


@celery_app.task(name="app.celery.tasks.financial_events.update_key_rate")
def update_key_rate() -> str:
    """
    Обновление ключевой ставки ЦБ
    """
    import asyncio

    async def _process():
        service = DailyEventsService(async_session_maker)
        await service.update_key_rate()
        return "Key rate updated successfully"

    try:
        result = asyncio.run(_process())
        logger.info("Key rate update completed")
        return result
    except Exception as e:
        logger.error(f"Error updating key rate: {e}")
        raise


@celery_app.task(name="app.celery.tasks.financial_events.apply_inflation")
def apply_inflation() -> str:
    """
    Применение инфляции к ценам товаров
    """
    import asyncio

    async def _process():
        service = DailyEventsService(async_session_maker)
        await service.apply_inflation()
        return "Inflation applied successfully"

    try:
        result = asyncio.run(_process())
        logger.info("Inflation application completed")
        return result
    except Exception as e:
        logger.error(f"Error applying inflation: {e}")
        raise


@celery_app.task(name="app.celery.tasks.financial_events.restore_user_energy")
def restore_user_energy() -> str:
    """
    Восстановление энергии пользователей
    """
    import asyncio

    async def _process():
        service = DailyEventsService(async_session_maker)
        await service.restore_user_energy()
        return "User energy restored successfully"

    try:
        result = asyncio.run(_process())
        logger.info("User energy restoration completed")
        return result
    except Exception as e:
        logger.error(f"Error restoring user energy: {e}")
        raise


@celery_app.task(name="app.celery.tasks.financial_events.run_daily_financial_events")
def run_daily_financial_events() -> str:
    """
    Запуск всех ежедневных финансовых событий
    """
    import asyncio

    async def _process():
        service = DailyEventsService(async_session_maker)

        # Начисляем проценты по накопительным счетам
        await service.process_savings_interest()

        # Начисляем проценты по вкладам
        await service.process_deposits_interest()

        # Обновляем ключевую ставку
        await service.update_key_rate()

        # Применяем инфляцию к ценам
        await service.apply_inflation()

        # Обновляем энергию пользователей
        await service.restore_user_energy()

        return "All daily financial events completed successfully"

    try:
        asyncio.run(_process())
        timestamp = datetime.now(timezone.utc).isoformat()
        message = f"Daily financial events completed at {timestamp}"
        logger.info(message)
        return message
    except Exception as e:
        logger.error(f"Error during daily financial events: {e}")
        raise
