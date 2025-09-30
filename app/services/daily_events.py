"""
Сервис для обработки ежедневных игровых событий
"""
import logging
import random
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import UserItem, User, Transaction, Item
from app.repositories import TransactionRepository, UserItemRepository, ItemRepository, WorldSettingRepository
from app.schemas.transaction import TransactionCreate, TransactionType

logger = logging.getLogger(__name__)


class DailyEventsService:
    """Сервис ежедневных игровых событий"""

    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def process_savings_interest(self):
        """
        Начисление процентов по накопительным счетам
        Начисление происходит ежедневно
        """
        async with self.session_factory() as session:
            try:
                # Получаем все накопительные счета
                stmt = select(UserItem).where(
                    UserItem.item_name.in_(["savings_basic", "savings_premium"])
                ).where(UserItem.amount > 0)

                result = await session.execute(stmt)
                savings_accounts = result.scalars().all()

                transaction_repo = TransactionRepository(session)

                for account in savings_accounts:
                    meta = account.meta or {}
                    annual_rate = meta.get("interest_rate", 5.0)

                    # Расчет дневных процентов
                    daily_rate = annual_rate / 365.0 / 100.0
                    interest_amount = int(account.amount * daily_rate)

                    if interest_amount > 0:
                        # Начисляем проценты
                        account.amount += interest_amount

                        # Создаем транзакцию
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

                await session.commit()
                logger.info(f"Processed interest for {len(savings_accounts)} savings accounts")

            except Exception as e:
                await session.rollback()
                logger.error(f"Error processing savings interest: {e}")
                raise

    async def process_deposits_interest(self):
        """
        Начисление процентов по вкладам
        В зависимости от способа выплаты процентов
        """
        async with self.session_factory() as session:
            try:
                # Получаем все активные вклады
                stmt = select(UserItem).where(
                    UserItem.item_name.in_(["deposit_kopit", "deposit_v_pluse"])
                ).where(UserItem.amount > 0)

                result = await session.execute(stmt)
                deposits = result.scalars().all()

                transaction_repo = TransactionRepository(session)
                user_item_repo = UserItemRepository(session)

                for deposit in deposits:
                    meta = deposit.meta or {}
                    payment_method = meta.get("interest_payment_method", "at_end")
                    annual_rate = meta.get("interest_rate", 10.0)

                    # Проверяем, не истек ли вклад
                    expires_at = datetime.fromisoformat(meta.get("expires_at", datetime.now(timezone.utc).isoformat()))
                    if datetime.now(timezone.utc) >= expires_at:
                        continue

                    # Расчет процентов в зависимости от метода выплаты
                    if payment_method == "monthly_capitalized":
                        # Ежемесячная капитализация (проверяем каждый день, начисляем раз в месяц)
                        opened_at = datetime.fromisoformat(meta.get("opened_at", datetime.now(timezone.utc).isoformat()))
                        days_since_open = (datetime.now(timezone.utc) - opened_at).days

                        # Если прошел месяц с открытия или с последней капитализации
                        if days_since_open % 30 == 0 and days_since_open > 0:
                            monthly_rate = annual_rate / 12.0 / 100.0
                            interest_amount = int(deposit.amount * monthly_rate)

                            if interest_amount > 0:
                                # Капитализируем проценты
                                deposit.amount += interest_amount

                                # Создаем транзакцию
                                await transaction_repo.create(
                                    TransactionCreate(
                                        user_id=deposit.user_id,
                                        instrument_id=str(deposit.id),
                                        amount=interest_amount,
                                        datetime_start=datetime.now(timezone.utc),
                                        type=TransactionType.DEPOSIT_INTEREST_PAYMENT,
                                        name=f"Капитализация процентов ({annual_rate}% годовых)",
                                    )
                                )

                    elif payment_method == "monthly_to_account":
                        # Ежемесячно на счет (не капитализируется)
                        opened_at = datetime.fromisoformat(meta.get("opened_at", datetime.now(timezone.utc).isoformat()))
                        days_since_open = (datetime.now(timezone.utc) - opened_at).days

                        if days_since_open % 30 == 0 and days_since_open > 0:
                            initial_amount = meta.get("initial_amount", deposit.amount)
                            monthly_rate = annual_rate / 12.0 / 100.0
                            interest_amount = int(initial_amount * monthly_rate)

                            if interest_amount > 0:
                                # Находим дебетовый счет пользователя
                                debet_stmt = select(UserItem).where(
                                    UserItem.user_id == deposit.user_id,
                                    UserItem.item_name.in_(["smart_mir", "supreme_mir"])
                                ).limit(1)

                                debet_result = await session.execute(debet_stmt)
                                debet_account = debet_result.scalar_one_or_none()

                                if debet_account:
                                    # Переводим проценты на дебетовый счет
                                    debet_account.amount += interest_amount

                                    # Создаем транзакцию выплаты процентов
                                    await transaction_repo.create(
                                        TransactionCreate(
                                            user_id=deposit.user_id,
                                            instrument_id=str(deposit.id),
                                            amount=0,  # Не меняем баланс вклада
                                            datetime_start=datetime.now(timezone.utc),
                                            type=TransactionType.DEPOSIT_INTEREST_PAYMENT,
                                            name=f"Выплата процентов ({annual_rate}% годовых)",
                                        )
                                    )

                                    # Создаем транзакцию зачисления на дебет
                                    await transaction_repo.create(
                                        TransactionCreate(
                                            user_id=deposit.user_id,
                                            instrument_id=str(debet_account.id),
                                            amount=interest_amount,
                                            datetime_start=datetime.now(timezone.utc),
                                            type=TransactionType.BANK,
                                            name="Зачисление процентов по вкладу",
                                        )
                                    )

                    # Для at_end проценты начисляются при закрытии вклада

                await session.commit()
                logger.info(f"Processed interest for {len(deposits)} deposits")

            except Exception as e:
                await session.rollback()
                logger.error(f"Error processing deposits interest: {e}")
                raise

    async def process_expired_deposits(self):
        """
        Автоматическое закрытие истекших вкладов
        """
        async with self.session_factory() as session:
            try:
                # Получаем все вклады
                stmt = select(UserItem).where(
                    UserItem.item_name.in_(["deposit_kopit", "deposit_v_pluse"])
                ).where(UserItem.amount > 0)

                result = await session.execute(stmt)
                deposits = result.scalars().all()

                transaction_repo = TransactionRepository(session)
                now = datetime.now(timezone.utc)

                for deposit in deposits:
                    meta = deposit.meta or {}
                    expires_at = datetime.fromisoformat(meta.get("expires_at", now.isoformat()))

                    # Если вклад истек
                    if now >= expires_at:
                        payment_method = meta.get("interest_payment_method", "at_end")

                        # Если проценты выплачиваются в конце
                        if payment_method == "at_end":
                            annual_rate = meta.get("interest_rate", 10.0)
                            term_days = meta.get("term_days", 30)
                            initial_amount = meta.get("initial_amount", deposit.amount)

                            # Расчет процентов за весь срок
                            total_rate = (annual_rate / 365.0) * term_days / 100.0
                            interest_amount = int(initial_amount * total_rate)

                            total_amount = initial_amount + interest_amount
                        else:
                            # Проценты уже были выплачены
                            total_amount = deposit.amount

                        # Находим дебетовый счет
                        debet_stmt = select(UserItem).where(
                            UserItem.user_id == deposit.user_id,
                            UserItem.item_name.in_(["smart_mir", "supreme_mir"])
                        ).limit(1)

                        debet_result = await session.execute(debet_stmt)
                        debet_account = debet_result.scalar_one_or_none()

                        if debet_account:
                            # Переводим средства на дебетовый счет
                            debet_account.amount += total_amount

                            # Создаем транзакцию закрытия вклада
                            await transaction_repo.create(
                                TransactionCreate(
                                    user_id=deposit.user_id,
                                    instrument_id=str(deposit.id),
                                    amount=-total_amount,
                                    datetime_start=now,
                                    type=TransactionType.DEPOSIT_CLOSE_MATURED,
                                    name=f"Автоматическое закрытие вклада по истечении срока",
                                )
                            )

                            # Создаем транзакцию зачисления на дебет
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
                            deposit.amount = 0

                            logger.info(f"Auto-closed expired deposit {deposit.id} for user {deposit.user_id}")

                await session.commit()

            except Exception as e:
                await session.rollback()
                logger.error(f"Error processing expired deposits: {e}")
                raise

    async def update_key_rate(self):
        """
        Обновление ключевой ставки ЦБ
        Моделирует изменение ключевой ставки с сохранением в world_settings
        """
        async with self.session_factory() as session:
            try:
                world_repo = WorldSettingRepository(session)

                # Получаем текущую ключевую ставку
                current_rate = await world_repo.get_key_rate()

                # Случайное изменение ставки в пределах ±0.25%
                change = random.uniform(-0.25, 0.25)
                new_rate = max(1.0, min(30.0, current_rate + change))

                # Сохраняем новую ставку
                await world_repo.set_key_rate(new_rate)
                await session.commit()

                logger.info(f"Key rate updated from {current_rate:.2f}% to {new_rate:.2f}%")

            except Exception as e:
                await session.rollback()
                logger.error(f"Error updating key rate: {e}")
                raise

    async def apply_inflation(self):
        """
        Применение инфляции к ценам товаров с использованием world_settings
        """
        async with self.session_factory() as session:
            try:
                world_repo = WorldSettingRepository(session)

                # Получаем годовой уровень инфляции и конвертируем в дневной
                annual_inflation = await world_repo.get_inflation_rate()
                daily_inflation = annual_inflation / 365.0  # Дневная инфляция

                # Получаем все товары с ценами
                stmt = select(Item).where(Item.price > 0)
                result = await session.execute(stmt)
                items = result.scalars().all()

                items_updated = 0
                for item in items:
                    # Применяем дневную инфляцию
                    inflation_factor = 1 + (daily_inflation / 100.0)
                    new_price = int(item.price * inflation_factor)

                    # Округляем до ближайших 10 копеек
                    new_price = (new_price // 10) * 10

                    if new_price != item.price:
                        item.price = new_price
                        items_updated += 1

                await session.commit()
                logger.info(f"Applied {daily_inflation:.4f}% daily inflation to {items_updated} items (annual: {annual_inflation:.2f}%)")

            except Exception as e:
                await session.rollback()
                logger.error(f"Error applying inflation: {e}")
                raise

    async def restore_user_energy(self):
        """
        Восстановление энергии пользователей
        """
        async with self.session_factory() as session:
            try:
                # Получаем всех пользователей
                stmt = select(User).where(User.energy < 100)  # Предполагаем максимум 100
                result = await session.execute(stmt)
                users = result.scalars().all()

                for user in users:
                    # Восстанавливаем 20 единиц энергии в день
                    user.energy = min(100, user.energy + 20)

                await session.commit()
                logger.info(f"Restored energy for {len(users)} users")

            except Exception as e:
                await session.rollback()
                logger.error(f"Error restoring user energy: {e}")
                raise