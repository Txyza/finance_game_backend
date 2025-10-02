"""
Сервис для обработки ежедневных (и периодических) финансовых игровых событий.
Перенесен в app/celery/tasks и использует только репозитории.
"""

import logging
import random
from datetime import datetime, timezone

from app.repositories import (
    TransactionRepository,
    WorldSettingRepository,
    UserItemRepository,
    ItemRepository,
    WorkRepository,
)
from app.schemas.transaction import TransactionCreate, TransactionType
from app.schemas.user_item import UserItemUpdate
from app.schemas.item import ItemUpdate
from app.schemas.work import WorkUpdate


from typing import cast
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base

from app.core.config import settings

logger = logging.getLogger(__name__)

DATABASE_URL = cast(str, settings.DATABASE_URL)


Base = declarative_base()


class DailyEventsService:
    """Сервис финансовых событий (проценты, инфляция, ключевая ставка)."""

    def __init__(self):
        engine = create_async_engine(DATABASE_URL, echo=settings.DEBUG, future=True)
        self.session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    async def process_savings_interest(self):
        """
        Начисление процентов по накопительным счетам.
        Начисление выполняется ежедневно. Год = 28 дней.
        """
        async with self.session_factory() as session:
            try:
                user_item_repo = UserItemRepository(session)
                transaction_repo = TransactionRepository(session)

                savings_accounts = await user_item_repo.list_active_savings_accounts()

                processed = 0
                for account in savings_accounts:
                    meta = account.meta or {}
                    annual_rate = float(meta.get("interest_rate", 5.0))

                    # Дневная ставка при годе в 28 дней
                    daily_rate = annual_rate / 28.0 / 100.0
                    interest_amount = int(account.amount * daily_rate)

                    if interest_amount > 0:
                        # Начисляем проценты на счет
                        new_amount = account.amount + interest_amount
                        await user_item_repo.update_amount(account.id, new_amount)

                        # Фиксируем транзакцию
                        await transaction_repo.create(
                            TransactionCreate(
                                user_id=account.user_id,
                                instrument_id=str(account.id),
                                amount=interest_amount,
                                datetime_start=datetime.now(timezone.utc),
                                type=TransactionType.SAVINGS_INTEREST,
                                name=f"Начисление процентов ({annual_rate}% годовых)",
                            )
                        )
                        processed += 1

                await session.commit()
                logger.info(
                    f"Processed interest for {processed} savings accounts (total scanned: {len(savings_accounts)})"
                )

            except Exception as e:
                await session.rollback()
                logger.error(f"Error processing savings interest: {e}")
                raise

    async def process_deposits_interest(self):
        """
        Начисление процентов по вкладам в зависимости от способа выплаты.
        - monthly_capitalized/monthly_to_account трактуем как сезон (неделя = 3 месяца).
        - Год = 28 дней => неделя = 7 дней, сезонная ставка = годовая/4.
        """
        async with self.session_factory() as session:
            try:
                user_item_repo = UserItemRepository(session)
                transaction_repo = TransactionRepository(session)

                deposits = await user_item_repo.list_active_deposits()

                for deposit in deposits:
                    meta = deposit.meta or {}
                    payment_method = meta.get("interest_payment_method", "at_end")
                    annual_rate = float(meta.get("interest_rate", 10.0))

                    # Прекращаем начисления, если срок истек
                    expires_at = datetime.fromisoformat(
                        meta.get("expires_at", datetime.now(timezone.utc).isoformat())
                    )
                    now = datetime.now(timezone.utc)
                    if now >= expires_at:
                        continue

                    # Обрабатываем периодические выплаты: неделя как 3 месяца
                    if payment_method in ("monthly_capitalized", "monthly_to_account"):
                        opened_at = datetime.fromisoformat(
                            meta.get("opened_at", now.isoformat())
                        )
                        days_since_open = (now - opened_at).days

                        # Выплачиваем раз в неделю (сезон)
                        if days_since_open > 0 and days_since_open % 7 == 0:
                            season_rate = (
                                annual_rate / 4.0 / 100.0
                            )  # 1 сезон = 1/4 года

                            if payment_method == "monthly_capitalized":
                                interest_amount = int(deposit.amount * season_rate)
                                if interest_amount > 0:
                                    new_amount = deposit.amount + interest_amount
                                    await user_item_repo.update_amount(
                                        deposit.id, new_amount
                                    )
                                    await transaction_repo.create(
                                        TransactionCreate(
                                            user_id=deposit.user_id,
                                            instrument_id=str(deposit.id),
                                            amount=interest_amount,
                                            datetime_start=now,
                                            type=TransactionType.DEPOSIT_INTEREST_PAYMENT,
                                            name=f"Капитализация процентов ({annual_rate}% годовых)",
                                        )
                                    )

                            else:  # monthly_to_account
                                initial_amount = int(
                                    meta.get("initial_amount", deposit.amount)
                                )
                                interest_amount = int(initial_amount * season_rate)
                                if interest_amount > 0:
                                    # Зачисляем проценты на первый дебетовый счет
                                    debet_account = (
                                        await user_item_repo.get_first_debet_account(
                                            deposit.user_id
                                        )
                                    )
                                    if debet_account:
                                        await user_item_repo.update_amount(
                                            debet_account.id,
                                            debet_account.amount + interest_amount,
                                        )
                                        # Транзакция для вклада (фиксация выплаты)
                                        await transaction_repo.create(
                                            TransactionCreate(
                                                user_id=deposit.user_id,
                                                instrument_id=str(deposit.id),
                                                amount=0,  # Баланс вклада неизменен
                                                datetime_start=now,
                                                type=TransactionType.DEPOSIT_INTEREST_PAYMENT,
                                                name=f"Выплата процентов ({annual_rate}% годовых)",
                                            )
                                        )
                                        # Транзакция зачисления на дебет
                                        await transaction_repo.create(
                                            TransactionCreate(
                                                user_id=deposit.user_id,
                                                instrument_id=str(debet_account.id),
                                                amount=interest_amount,
                                                datetime_start=now,
                                                type=TransactionType.BANK,
                                                name="Зачисление процентов по вкладу",
                                            )
                                        )

                await session.commit()
                logger.info(f"Processed periodic interest for {len(deposits)} deposits")

            except Exception as e:
                await session.rollback()
                logger.error(f"Error processing deposits interest: {e}")
                raise

    async def process_expired_deposits(self):
        """
        Автоматическое закрытие истекших вкладов.
        Для способа at_end проценты считаются по ставке с годом=28 дней.
        """
        async with self.session_factory() as session:
            try:
                user_item_repo = UserItemRepository(session)
                transaction_repo = TransactionRepository(session)
                now = datetime.now(timezone.utc)

                deposits = await user_item_repo.list_active_deposits()

                for deposit in deposits:
                    meta = deposit.meta or {}
                    expires_at = datetime.fromisoformat(
                        meta.get("expires_at", now.isoformat())
                    )

                    if now >= expires_at:
                        payment_method = meta.get("interest_payment_method", "at_end")

                        if payment_method == "at_end":
                            annual_rate = float(meta.get("interest_rate", 10.0))
                            term_days = int(meta.get("term_days", 7))
                            initial_amount = int(
                                meta.get("initial_amount", deposit.amount)
                            )

                            # Ставка за весь срок при годе=28 дней
                            total_rate = (annual_rate / 28.0) * term_days / 100.0
                            interest_amount = int(initial_amount * total_rate)
                            total_amount = initial_amount + interest_amount
                        else:
                            # Проценты уже выплачивались по ходу срока
                            total_amount = deposit.amount

                        debet_account = await user_item_repo.get_first_debet_account(
                            deposit.user_id
                        )

                        if debet_account:
                            # Переводим средства на дебетовый счет
                            await user_item_repo.update_amount(
                                debet_account.id, debet_account.amount + total_amount
                            )

                            # Транзакция закрытия вклада
                            await transaction_repo.create(
                                TransactionCreate(
                                    user_id=deposit.user_id,
                                    instrument_id=str(deposit.id),
                                    amount=-total_amount,
                                    datetime_start=now,
                                    type=TransactionType.DEPOSIT_CLOSE_MATURED,
                                    name="Автоматическое закрытие вклада по истечении срока",
                                )
                            )

                            # Транзакция зачисления на дебет
                            await transaction_repo.create(
                                TransactionCreate(
                                    user_id=deposit.user_id,
                                    instrument_id=str(debet_account.id),
                                    amount=total_amount,
                                    datetime_start=now,
                                    type=TransactionType.BANK,
                                    name="Зачисление средств от закрытого вклада",
                                )
                            )

                            # Обнуляем вклад
                            await user_item_repo.update_amount(deposit.id, 0)

                            logger.info(
                                f"Auto-closed expired deposit {deposit.id} for user {deposit.user_id}"
                            )

                await session.commit()

            except Exception as e:
                await session.rollback()
                logger.error(f"Error processing expired deposits: {e}")
                raise

    async def update_key_rate(self):
        """
        Еженедельное обновление ключевой ставки + пересчёт ставок накопительных.
        - Ключевая: случайное изменение в пределах ±3 п.п., коридор [1, 30].
        - Накопительные: ставка = k * key_rate, где k зависит от счёта:
          savings_basic -> 60% от ключевой; savings_premium -> 80% от ключевой.
        """
        async with self.session_factory() as session:
            try:
                world_repo = WorldSettingRepository(session)

                current_rate = float(await world_repo.get_key_rate())

                change = random.randint(-3, 3)
                new_rate = max(1.0, min(30.0, current_rate + change))

                # 1) Обновляем ключевую ставку
                await world_repo.set_key_rate(new_rate)

                # 2) Обновляем инфляцию вместе с ключевой
                #    Диапазон: [key_rate - 3 п.п., key_rate + 1 п.п.]
                infl_min = max(0.0, new_rate - 3.0)
                infl_max = new_rate + 1.0
                new_inflation = round(random.uniform(infl_min, infl_max), 2)
                await world_repo.set_inflation_rate(new_inflation)
                avg_inflation = (
                    await world_repo.update_average_inflation_with_weekly_sample(
                        new_inflation
                    )
                )

                # 3) Пересчитываем ставки накопительных счетов
                user_item_repo = UserItemRepository(session)
                savings_accounts = await user_item_repo.list_savings_accounts()

                updated_cnt = 0
                for account in savings_accounts:
                    name = account.item_name
                    # По умолчанию считаем basic=60%, premium=80%
                    if name.endswith("premium"):
                        ratio = 0.80
                    else:
                        ratio = 0.60

                    new_interest = round(new_rate * ratio, 2)
                    meta = dict(account.meta or {})
                    if float(meta.get("interest_rate", -1.0)) != new_interest:
                        meta["interest_rate"] = new_interest
                        await user_item_repo.update(
                            account.id, UserItemUpdate(meta=meta)
                        )
                        updated_cnt += 1

                await session.commit()

                logger.info(
                    (
                        "Key rate updated from %.2f%% to %.2f%% (Δ %+d п.п.); "
                        "inflation set to %.2f%% (avg %.2f%%); recalculated savings rates for %d accounts"
                    )
                    % (
                        current_rate,
                        new_rate,
                        change,
                        new_inflation,
                        avg_inflation,
                        updated_cnt,
                    )
                )

            except Exception as e:
                await session.rollback()
                logger.error(f"Error updating key rate: {e}")
                raise

    async def apply_inflation(self):
        """
        Применение инфляции к ценам товаров.
        Год = 28 дней, применяем дневную долю инфляции.
        """
        async with self.session_factory() as session:
            try:
                world_repo = WorldSettingRepository(session)
                item_repo = ItemRepository(session)

                annual_inflation = float(await world_repo.get_inflation_rate())
                daily_inflation = (
                    annual_inflation / 28.0
                )  # Дневная инфляция (в процентах)

                items = await item_repo.list_priced_items()

                items_updated = 0
                for item in items:
                    inflation_factor = 1 + (daily_inflation / 100.0)
                    new_price = int(item.price * inflation_factor)
                    new_price = (new_price // 10) * 10  # Округление до 10 копеек

                    if new_price != item.price:
                        await item_repo.update(
                            item.name, data=ItemUpdate(price=new_price)
                        )
                        items_updated += 1

                await session.commit()
                logger.info(
                    f"Applied {daily_inflation:.4f}% daily inflation to {items_updated} items (annual: {annual_inflation:.2f}%)"
                )

            except Exception as e:
                await session.rollback()
                logger.error(f"Error applying inflation: {e}")
                raise

    async def index_work_max_amount_yearly(self):
        """
        Ежегодная (раз в 28 дней) индексация work.max_amount по среднегодовой инфляции.
        Формула: new_max = round(old_max * (1 + avg_inflation/100)).
        """
        async with self.session_factory() as session:
            try:
                world_repo = WorldSettingRepository(session)
                work_repo = WorkRepository(session)

                avg_infl = float(await world_repo.get_average_inflation_rate())
                factor = 1.0 + avg_infl / 100.0

                works = await work_repo.list_many(limit=10_000)
                updated = 0
                for w in works:
                    new_max = int(round(w.max_amount * factor))
                    if new_max != w.max_amount:
                        await work_repo.update(w.name, WorkUpdate(max_amount=new_max))
                        updated += 1

                await session.commit()
                logger.info(
                    f"Indexed work.max_amount for {updated} works by avg inflation {avg_infl:.2f}% (factor {factor:.6f})"
                )
            except Exception as e:
                await session.rollback()
                logger.error(f"Error indexing work max_amount: {e}")
                raise
