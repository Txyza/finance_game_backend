import random
import string
from datetime import datetime, timezone, timedelta
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import CurrentUser, SessionDep
from app.api.schemas.deposit import (
    DepositCloseResponse,
    DepositCreateRequest,
    DepositCreateResponse,
    DepositDetail,
    DepositListResponse,
    DepositTransaction,
    DepositTransactionsResponse,
    InterestPaymentMethod,
)
from app.repositories import ItemRepository, TransactionRepository, UserItemRepository
from app.schemas.transaction import TransactionCreate, TransactionType
from app.schemas.user_item import UserItemCreate, UserItemUpdate
from app.api.utils.items import attach_items, find_primary_debet_item

router = APIRouter(prefix="/deposits", tags=["deposits"])


def _generate_deposit_account_number() -> str:
    """
    Генерирует случайный номер депозитного счета

    Returns:
        str: Номер счета из 6 цифр
    """
    return ''.join(random.choices(string.digits, k=6))


def _get_deposit_display_name(item_name: str, meta: dict = None) -> str:
    """
    Возвращает человекочитаемое название вклада

    Args:
        item_name: Техническое имя вклада
        meta: Метаданные вклада

    Returns:
        str: Человекочитаемое название
    """
    # Маппинг технических имен на человекочитаемые
    name_mapping = {
        "deposit_kopit": "Вклад «Копить»",
        "deposit_v_pluse": "Вклад «В Плюсе»",
    }

    # Если есть метаданные с названием, используем его
    if meta and meta.get("deposit_name"):
        return meta["deposit_name"]

    # Иначе используем маппинг или базовое имя
    return name_mapping.get(item_name, "Вклад")


def _calculate_days_remaining(expires_at: datetime) -> int:
    """
    Вычисляет количество дней до окончания вклада

    Args:
        expires_at: Дата окончания вклада

    Returns:
        int: Количество дней до окончания (минимум 0)
    """
    now = datetime.now(timezone.utc)
    if expires_at <= now:
        return 0
    delta = expires_at - now
    return max(0, delta.days)


@router.get("", response_model=DepositListResponse)
async def list_deposits(
    current_user: CurrentUser,
    session: SessionDep,
) -> DepositListResponse:
    """
    Получить список вкладов пользователя

    Args:
        current_user: Текущий авторизованный пользователь
        session: Сессия базы данных

    Returns:
        DepositListResponse: Список вкладов с основной информацией
    """

    user_item_repository = UserItemRepository(session)
    user_items = await user_item_repository.list_by_user(current_user.id)

    # Фильтруем только вклады
    deposits = [
        item for item in user_items
        if item.item_name.startswith("deposit_") or
           (item.meta and item.meta.get("account_type") == "deposit")
    ]

    deposit_list = []
    for deposit in deposits:
        meta = deposit.meta or {}
        expires_at = datetime.fromisoformat(meta.get("expires_at", datetime.now(timezone.utc).isoformat()))

        deposit_list.append({
            "id": deposit.id,
            "deposit_name": _get_deposit_display_name(deposit.item_name, meta),
            "account_number": meta.get("account_number", "000000"),
            "current_interest_rate": meta.get("interest_rate", 0.0),
            "balance": deposit.amount,
            "days_remaining": _calculate_days_remaining(expires_at),
        })

    return DepositListResponse(deposits=deposit_list)


@router.post("", response_model=DepositCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_deposit(
    payload: DepositCreateRequest,
    current_user: CurrentUser,
    session: SessionDep,
) -> DepositCreateResponse:
    """
    Создать новый вклад

    Args:
        payload: Данные для создания вклада (название, сумма, срок, ставка, способ выплаты)
        current_user: Текущий авторизованный пользователь
        session: Сессия базы данных

    Returns:
        DepositCreateResponse: ID созданного вклада, номер счета и дата окончания

    Raises:
        HTTPException: 400 если некорректные данные (ставка превышает ключевую)
    """

    user_item_repository = UserItemRepository(session)
    transaction_repository = TransactionRepository(session)
    item_repository = ItemRepository(session)

    # Получаем дебетовый счет пользователя
    user_items = await user_item_repository.list_by_user(current_user.id)
    inventory = await attach_items(user_items, item_repository)
    debet_entry = find_primary_debet_item(inventory)

    if not debet_entry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="У пользователя нет дебетового счета",
        )

    debet_item, _ = debet_entry

    # Проверяем достаточность средств на дебетовом счете
    if debet_item.amount < payload.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недостаточно средств на дебетовом счете",
        )

    # Генерируем номер счета и вычисляем дату окончания
    account_number = _generate_deposit_account_number()
    opened_at = datetime.now(timezone.utc)
    expires_at = opened_at + timedelta(days=payload.term_days)

    # Определяем базовое имя из каталога
    deposit_name_lower = payload.deposit_name.lower()
    if "копить" in deposit_name_lower or "kopit" in deposit_name_lower:
        catalog_item_name = "deposit_kopit"
        display_name = "Вклад «Копить»"
    elif "плюс" in deposit_name_lower or "plus" in deposit_name_lower:
        catalog_item_name = "deposit_v_pluse"
        display_name = "Вклад «В Плюсе»"
    else:
        catalog_item_name = "deposit_kopit"  # По умолчанию используем Копить
        display_name = payload.deposit_name

    # Создаем метаданные вклада
    deposit_meta = {
        "account_type": "deposit",
        "deposit_name": display_name,
        "account_number": account_number,
        "interest_rate": payload.interest_rate,
        "opened_at": opened_at.isoformat(),
        "expires_at": expires_at.isoformat(),
        "term_days": payload.term_days,
        "interest_payment_method": payload.interest_payment_method.value,
        "initial_amount": payload.amount,
    }

    # Списываем с дебетового счета
    await user_item_repository.update_amount(debet_item.id, debet_item.amount - payload.amount)

    # Создаем вклад как UserItem
    user_item = await user_item_repository.create(
        UserItemCreate(
            user_id=current_user.id,
            item_name=catalog_item_name,
            amount=payload.amount,
            meta=deposit_meta,
        )
    )

    # Устанавливаем дату истечения для автоматического завершения
    await user_item_repository.update(
        user_item.id,
        UserItemUpdate(expaired_at=expires_at)
    )

    # Создаем транзакцию списания с дебетового счета
    await transaction_repository.create(
        TransactionCreate(
            user_id=current_user.id,
            instrument_id=str(debet_item.id),
            amount=-payload.amount,  # Отрицательная сумма для списания
            datetime_start=opened_at,
            type=TransactionType.BANK,
            name=f"Открытие {display_name}",
        )
    )

    # Создаем транзакцию открытия вклада
    await transaction_repository.create(
        TransactionCreate(
            user_id=current_user.id,
            instrument_id=str(user_item.id),
            amount=payload.amount,
            datetime_start=opened_at,
            type=TransactionType.DEPOSIT_OPEN,
            name=f"Открытие {display_name}",
        )
    )

    return DepositCreateResponse(
        deposit_id=user_item.id,
        account_number=account_number,
        expires_at=expires_at,
    )


@router.get("/{deposit_id}", response_model=DepositDetail)
async def get_deposit_detail(
    deposit_id: UUID,
    current_user: CurrentUser,
    session: SessionDep,
) -> DepositDetail:
    """
    Получить детальную карточку вклада

    Args:
        deposit_id: Уникальный идентификатор вклада
        current_user: Текущий авторизованный пользователь
        session: Сессия базы данных

    Returns:
        DepositDetail: Полная информация о вкладе

    Raises:
        HTTPException: 404 если вклад не найден или не принадлежит пользователю
    """

    user_item_repository = UserItemRepository(session)
    deposit = await user_item_repository.get_by_id(deposit_id)

    if not deposit or deposit.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вклад не найден",
        )

    # Проверяем, что это вклад
    meta = deposit.meta or {}
    if meta.get("account_type") != "deposit":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Это не вклад",
        )

    expires_at = datetime.fromisoformat(meta.get("expires_at", datetime.now(timezone.utc).isoformat()))
    opened_at = datetime.fromisoformat(meta.get("opened_at", datetime.now(timezone.utc).isoformat()))

    return DepositDetail(
        id=deposit.id,
        deposit_name=_get_deposit_display_name(deposit.item_name, meta),
        account_number=meta.get("account_number", "000000"),
        current_interest_rate=meta.get("interest_rate", 0.0),
        balance=deposit.amount,
        opened_at=opened_at,
        expires_at=expires_at,
        days_remaining=_calculate_days_remaining(expires_at),
        interest_payment_method=InterestPaymentMethod(meta.get("interest_payment_method", "at_end")),
    )


@router.post("/{deposit_id}/close", response_model=DepositCloseResponse)
async def close_deposit_early(
    deposit_id: UUID,
    current_user: CurrentUser,
    session: SessionDep,
) -> DepositCloseResponse:
    """
    Досрочно закрыть вклад

    При досрочном закрытии проценты рассчитываются по ставке 0,01% годовых.
    Пользователь получает только первоначальную сумму.

    Args:
        deposit_id: Уникальный идентификатор вклада
        current_user: Текущий авторизованный пользователь
        session: Сессия базы данных

    Returns:
        DepositCloseResponse: ID закрытого вклада и переведенная сумма

    Raises:
        HTTPException: 404 если вклад не найден или не принадлежит пользователю
    """

    user_item_repository = UserItemRepository(session)
    transaction_repository = TransactionRepository(session)
    item_repository = ItemRepository(session)

    # Проверяем существование вклада
    deposit = await user_item_repository.get_by_id(deposit_id)
    if not deposit or deposit.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вклад не найден",
        )

    # Получаем дебетовый счет пользователя
    user_items = await user_item_repository.list_by_user(current_user.id)
    inventory = await attach_items(user_items, item_repository)
    debet_entry = find_primary_debet_item(inventory)

    if not debet_entry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="У пользователя нет дебетового счета",
        )

    debet_item, _ = debet_entry

    meta = deposit.meta or {}
    initial_amount = meta.get("initial_amount", deposit.amount)
    expires_at = datetime.fromisoformat(meta.get("expires_at", datetime.now(timezone.utc).isoformat()))

    # Проверяем, не завершен ли уже вклад
    now = datetime.now(timezone.utc)
    is_early_closure = now < expires_at

    # Получаем красивое название вклада
    deposit_display_name = _get_deposit_display_name(deposit.item_name, meta)

    if is_early_closure:
        # Досрочное закрытие - возвращаем только первоначальную сумму
        transferred_amount = initial_amount
        penalty_applied = True
        penalty_message = "При досрочном закрытии проценты не выплачиваются. Возвращена только первоначальная сумма."
        transaction_type = TransactionType.DEPOSIT_CLOSE_EARLY
        transaction_name = f"Досрочное закрытие {deposit_display_name}"
    else:
        # Вклад завершился по сроку
        transferred_amount = deposit.amount
        penalty_applied = False
        penalty_message = "Вклад закрыт по истечении срока. Выплачены все проценты."
        transaction_type = TransactionType.DEPOSIT_CLOSE_MATURED
        transaction_name = f"Закрытие {deposit_display_name} по истечении срока"

    # Пополняем дебетовый счет
    await user_item_repository.update_amount(debet_item.id, debet_item.amount + transferred_amount)

    # Обнуляем баланс (закрываем вклад)
    await user_item_repository.update_amount(deposit_id, 0)

    # Создаем транзакцию закрытия вклада
    await transaction_repository.create(
        TransactionCreate(
            user_id=current_user.id,
            instrument_id=str(deposit_id),
            amount=-transferred_amount,  # Отрицательная сумма для вывода средств
            datetime_start=now,
            type=transaction_type,
            name=transaction_name,
        )
    )

    # Создаем транзакцию пополнения дебетового счета
    await transaction_repository.create(
        TransactionCreate(
            user_id=current_user.id,
            instrument_id=str(debet_item.id),
            amount=transferred_amount,
            datetime_start=now,
            type=TransactionType.BANK,
            name=f"Закрытие {deposit_display_name}",
        )
    )

    return DepositCloseResponse(
        deposit_id=deposit_id,
        transferred_amount=transferred_amount,
        penalty_applied=penalty_applied,
        penalty_message=penalty_message,
    )


@router.get("/{deposit_id}/transactions", response_model=DepositTransactionsResponse)
async def list_deposit_transactions(
    deposit_id: UUID,
    current_user: CurrentUser,
    session: SessionDep,
) -> DepositTransactionsResponse:
    """
    Получить список транзакций по вкладу

    Args:
        deposit_id: Уникальный идентификатор вклада
        current_user: Текущий авторизованный пользователь
        session: Сессия базы данных

    Returns:
        DepositTransactionsResponse: Список транзакций с названием, суммой и датой

    Note:
        Исключаются транзакции с нулевой суммой

    Raises:
        HTTPException: 404 если вклад не найден или не принадлежит пользователю
    """

    user_item_repository = UserItemRepository(session)
    transaction_repository = TransactionRepository(session)

    # Проверяем существование вклада
    deposit = await user_item_repository.get_by_id(deposit_id)
    if not deposit or deposit.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вклад не найден",
        )

    # Получаем транзакции по этому вкладу
    transactions = await transaction_repository.list_by_instrument_id(str(deposit_id))

    # Преобразуем в схему ответа, исключая транзакции с нулевой суммой
    deposit_transactions = []
    for transaction in transactions:
        if transaction.amount != 0:  # Исключаем нулевые транзакции
            deposit_transactions.append(
                DepositTransaction(
                    id=transaction.id,
                    name=transaction.name,
                    amount=transaction.amount,
                    datetime_start=transaction.datetime_start,
                )
            )

    return DepositTransactionsResponse(
        deposit_id=deposit_id,
        transactions=deposit_transactions,
    )