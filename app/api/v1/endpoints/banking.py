from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import CurrentUser, SessionDep
from app.api.schemas.banking import (
    BankingInstrument,
    BankingInstrumentsResponse,
    InstrumentType,
)
from app.repositories import ItemRepository, UserItemRepository
from app.api.utils.items import attach_items
from app.schemas import ItemType

router = APIRouter(prefix="/banking", tags=["banking"])


def _calculate_days_remaining(expires_at: datetime) -> int:
    """
    Вычисляет количество дней до окончания

    Args:
        expires_at: Дата окончания

    Returns:
        int: Количество дней до окончания (минимум 0)
    """
    now = datetime.now(timezone.utc)
    if expires_at <= now:
        return 0
    delta = expires_at - now
    return max(0, delta.days)


def _get_display_name(item_name: str, item_type: ItemType, meta: dict = None) -> str:
    """
    Возвращает человекочитаемое название инструмента

    Args:
        item_name: Техническое имя инструмента
        item_type: Тип инструмента
        meta: Метаданные

    Returns:
        str: Человекочитаемое название
    """
    name_mapping = {
        # Дебетовые карты
        "smart_mir": "Умная карта Мир",
        "supreme_mir": "Mir Supreme",
        # Накопительные счета
        "savings_basic": "Накопительный счет Базовый",
        "savings_premium": "Накопительный счет Премиум",
        # Вклады
        "deposit_kopit": "Вклад «Копить»",
        "deposit_v_pluse": "Вклад «В Плюсе»",
    }

    # Если есть метаданные с названием для вкладов, используем его
    if item_type == ItemType.DEPOSIT and meta and meta.get("deposit_name"):
        return meta["deposit_name"]

    return name_mapping.get(item_name, item_name)


@router.get("/instruments", response_model=BankingInstrumentsResponse)
async def get_banking_instruments(
    current_user: CurrentUser,
    session: SessionDep,
) -> BankingInstrumentsResponse:
    """
    Получить все банковские инструменты пользователя

    Возвращает список всех дебетовых карт, накопительных счетов и вкладов пользователя,
    сгруппированных по типам, с общим балансом.

    Args:
        current_user: Текущий авторизованный пользователь
        session: Сессия базы данных

    Returns:
        BankingInstrumentsResponse: Списки инструментов по категориям и общий баланс
    """

    user_item_repository = UserItemRepository(session)
    item_repository = ItemRepository(session)

    # Получаем все предметы пользователя
    user_items = await user_item_repository.list_by_user(current_user.id)
    inventory = await attach_items(user_items, item_repository)

    debit_cards = []
    savings_accounts = []
    deposits = []
    total_balance = 0

    for user_item, item in inventory:
        meta = user_item.meta or {}

        # Определяем тип инструмента
        if item.type == ItemType.DEBET:
            # Дебетовая карта
            instrument = BankingInstrument(
                id=user_item.id,
                type=InstrumentType.DEBIT_CARD,
                name=_get_display_name(item.name, item.type, meta),
                account_number=meta.get("card_number", "****"),
                balance=user_item.amount,
                opened_at=datetime.fromisoformat(meta.get("opened_at", datetime.now(timezone.utc).isoformat())),
            )
            debit_cards.append(instrument)
            total_balance += user_item.amount

        elif item.type == ItemType.SAVINGS or item.name.startswith("savings_"):
            # Накопительный счет
            instrument = BankingInstrument(
                id=user_item.id,
                type=InstrumentType.SAVINGS_ACCOUNT,
                name=_get_display_name(item.name, ItemType.SAVINGS, meta),
                account_number=meta.get("account_number", "000000"),
                balance=user_item.amount,
                interest_rate=meta.get("interest_rate", 5.0),
                opened_at=datetime.fromisoformat(meta.get("opened_at", datetime.now(timezone.utc).isoformat())),
                expires_at=user_item.expaired_at,
            )
            savings_accounts.append(instrument)
            total_balance += user_item.amount

        elif item.type == ItemType.DEPOSIT or item.name.startswith("deposit_"):
            # Вклад
            expires_at = datetime.fromisoformat(meta.get("expires_at", datetime.now(timezone.utc).isoformat()))
            instrument = BankingInstrument(
                id=user_item.id,
                type=InstrumentType.DEPOSIT,
                name=_get_display_name(item.name, ItemType.DEPOSIT, meta),
                account_number=meta.get("account_number", "000000"),
                balance=user_item.amount,
                interest_rate=meta.get("interest_rate", 0.0),
                opened_at=datetime.fromisoformat(meta.get("opened_at", datetime.now(timezone.utc).isoformat())),
                expires_at=expires_at,
                days_remaining=_calculate_days_remaining(expires_at),
            )
            deposits.append(instrument)
            total_balance += user_item.amount

    return BankingInstrumentsResponse(
        debit_cards=debit_cards,
        savings_accounts=savings_accounts,
        deposits=deposits,
        total_balance=total_balance,
    )