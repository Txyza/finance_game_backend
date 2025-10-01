import random
import string
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import CurrentUser, SessionDep
from app.api.schemas.savings import (
    SavingsAccountCloseResponse,
    SavingsAccountCreateRequest,
    SavingsAccountCreateResponse,
    SavingsAccountDetail,
    SavingsAccountListItem,
    SavingsAccountListResponse,
    SavingsAccountOperationRequest,
    SavingsAccountTransaction,
    SavingsAccountTransactionsResponse,
    SavingsAvailableProduct,
    SavingsAvailableResponse,
)
from app.repositories import (
    ItemRepository,
    TransactionRepository,
    UserItemRepository,
    WorldSettingRepository,
)
from app.schemas.transaction import TransactionCreate, TransactionType
from app.schemas.user_item import UserItemCreate
from app.api.utils.items import attach_items, find_primary_debet_item

router = APIRouter(prefix="/savings", tags=["savings"])


def _generate_account_number() -> str:
    """
    Генерирует случайный номер накопительного счета

    Returns:
        str: Номер счета из 6 цифр
    """
    return "".join(random.choices(string.digits, k=6))


def _get_savings_display_name(account_type: str) -> str:
    """
    Возвращает человекочитаемое название накопительного счета

    Args:
        account_type: Тип счета (basic, premium)

    Returns:
        str: Человекочитаемое название
    """
    name_mapping = {
        "basic": "Накопительный счет Basic",
        "premium": "Накопительный счет Premium",
    }
    return name_mapping.get(account_type, "Накопительный счет")


def _get_interest_ratio(account_type: str) -> float:
    """Коэффициент от ключевой ставки по типу счёта.

    basic -> 0.60 (60%), premium -> 0.80 (80%).
    Для неизвестных типов возвращаем 0.60.
    """
    ratios = {
        "basic": 0.60,
        "premium": 0.80,
    }
    return ratios.get(account_type, 0.60)


@router.get("", response_model=SavingsAccountListResponse)
async def list_savings_accounts(
    current_user: CurrentUser,
    session: SessionDep,
) -> SavingsAccountListResponse:
    """
    Получить список накопительных счетов пользователя

    Args:
        current_user: Текущий авторизованный пользователь
        session: Сессия базы данных

    Returns:
        SavingsAccountListResponse: Список накопительных счетов с основной информацией
    """

    user_item_repository = UserItemRepository(session)
    user_items = await user_item_repository.list_by_user(current_user.id)

    # Фильтруем только накопительные счета (можно добавить условие по item_name или meta)
    savings_accounts = [
        item
        for item in user_items
        if item.item_name.startswith("savings_")
        or (item.meta and item.meta.get("account_type") == "savings")
    ]

    accounts: list[SavingsAccountListItem] = []
    for account in savings_accounts:
        meta = account.meta or {}
        account_type = account.item_name.replace(
            "savings_", ""
        )  # Извлекаем тип из item_name
        accounts.append(
            SavingsAccountListItem(
                id=account.id,
                account_name=_get_savings_display_name(account_type),
                account_number=meta.get("account_number", "000000"),
                current_interest_rate=meta.get("interest_rate", 5.0),
                balance=account.amount,
            )
        )

    return SavingsAccountListResponse(accounts=accounts)


@router.post(
    "", response_model=SavingsAccountCreateResponse, status_code=status.HTTP_201_CREATED
)
async def create_savings_account(
    payload: SavingsAccountCreateRequest,
    current_user: CurrentUser,
    session: SessionDep,
) -> SavingsAccountCreateResponse:
    """
    Создать новый накопительный счет

    Args:
        payload: Данные для создания счета (тип счета, начальный депозит)
        current_user: Текущий авторизованный пользователь
        session: Сессия базы данных

    Returns:
        SavingsAccountCreateResponse: ID созданного счета и его номер

    Raises:
        HTTPException: 400 если некорректные данные
    """

    user_item_repository = UserItemRepository(session)
    transaction_repository = TransactionRepository(session)
    world_repository = WorldSettingRepository(session)

    # Генерируем номер счета
    account_number = _generate_account_number()
    # Рассчитываем стартовую ставку от ключевой
    key_rate = await world_repository.get_key_rate()
    interest_rate = round(key_rate * _get_interest_ratio(payload.account_type), 2)

    # Создаем накопительный счет как UserItem
    account_meta = {
        "account_type": "savings",
        "account_number": account_number,
        "interest_rate": interest_rate,
        "opened_at": datetime.now(timezone.utc).isoformat(),
    }

    user_item = await user_item_repository.create(
        UserItemCreate(
            user_id=current_user.id,
            item_name=f"savings_{payload.account_type}",
            amount=payload.initial_deposit,
            meta=account_meta,
        )
    )

    # Если есть начальный депозит, создаем транзакцию
    if payload.initial_deposit > 0:
        await transaction_repository.create(
            TransactionCreate(
                user_id=current_user.id,
                instrument_id=str(user_item.id),
                amount=payload.initial_deposit,
                datetime_start=datetime.now(timezone.utc),
                type=TransactionType.SAVINGS_DEPOSIT,
                name="Начальное пополнение счета",
            )
        )

    return SavingsAccountCreateResponse(
        account_id=user_item.id,
        account_number=account_number,
    )


@router.get("/available", response_model=SavingsAvailableResponse)
async def list_available_savings_products(
    session: SessionDep,
) -> SavingsAvailableResponse:
    """
    Список доступных типов накопительных счетов с текущими ставками (от ключевой).

    Возвращает пары (тип, отображаемое имя, ставка), чтобы UI мог показать
    пользователю актуальную ставку перед созданием счета.
    """

    world_repository = WorldSettingRepository(session)
    key_rate = await world_repository.get_key_rate()

    types = ["basic", "premium"]
    products: list[SavingsAvailableProduct] = []
    for t in types:
        rate = round(key_rate * _get_interest_ratio(t), 2)
        products.append(
            SavingsAvailableProduct(
                account_type=t,
                account_name=_get_savings_display_name(t),
                interest_rate=rate,
            )
        )

    return SavingsAvailableResponse(products=products)


@router.get("/{account_id}", response_model=SavingsAccountDetail)
async def get_savings_account_detail(
    account_id: UUID,
    current_user: CurrentUser,
    session: SessionDep,
) -> SavingsAccountDetail:
    """
    Получить детальную карточку накопительного счета

    Args:
        account_id: Уникальный идентификатор накопительного счета
        current_user: Текущий авторизованный пользователь
        session: Сессия базы данных

    Returns:
        SavingsAccountDetail: Полная информация о счете (номер, ставка, баланс, даты)

    Raises:
        HTTPException: 404 если счет не найден или не принадлежит пользователю
    """

    user_item_repository = UserItemRepository(session)
    account = await user_item_repository.get_by_id(account_id)

    if not account or account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Накопительный счет не найден",
        )

    # Проверяем, что это накопительный счет
    meta = account.meta or {}
    if meta.get("account_type") != "savings":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Это не накопительный счет",
        )

    account_type = account.item_name.replace(
        "savings_", ""
    )  # Извлекаем тип из item_name

    return SavingsAccountDetail(
        id=account.id,
        account_name=_get_savings_display_name(account_type),
        account_number=meta.get("account_number", "000000"),
        current_interest_rate=meta.get("interest_rate", 5.0),
        balance=account.amount,
        opened_at=datetime.fromisoformat(
            meta.get("opened_at", datetime.now(timezone.utc).isoformat())
        ),
        expires_at=account.expaired_at,
    )


@router.post("/{account_id}/deposit", status_code=status.HTTP_202_ACCEPTED)
async def deposit_to_savings_account(
    account_id: UUID,
    payload: SavingsAccountOperationRequest,
    current_user: CurrentUser,
    session: SessionDep,
) -> dict:
    """
    Пополнить накопительный счет

    Args:
        account_id: Уникальный идентификатор накопительного счета
        payload: Сумма пополнения в копейках (должна быть больше 0)
        current_user: Текущий авторизованный пользователь
        session: Сессия базы данных

    Returns:
        dict: Сообщение об успешном пополнении

    Raises:
        HTTPException: 404 если счет не найден или не принадлежит пользователю
    """

    user_item_repository = UserItemRepository(session)
    transaction_repository = TransactionRepository(session)
    item_repository = ItemRepository(session)

    # Проверяем существование счета
    account = await user_item_repository.get_by_id(account_id)
    if not account or account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Накопительный счет не найден",
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

    # Проверяем достаточность средств на дебетовом счете
    if debet_item.amount < payload.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недостаточно средств на дебетовом счете",
        )

    # Списываем с дебетового счета
    await user_item_repository.update_amount(
        debet_item.id, debet_item.amount - payload.amount
    )

    # Пополняем накопительный счет
    await user_item_repository.update_amount(
        account_id, account.amount + payload.amount
    )

    # Создаем транзакцию списания с дебетового счета
    await transaction_repository.create(
        TransactionCreate(
            user_id=current_user.id,
            instrument_id=str(debet_item.id),
            amount=-payload.amount,  # Отрицательная сумма для списания
            datetime_start=datetime.now(timezone.utc),
            type=TransactionType.BANK,
            name="Перевод на накопительный счет",
        )
    )

    # Создаем транзакцию пополнения накопительного счета
    await transaction_repository.create(
        TransactionCreate(
            user_id=current_user.id,
            instrument_id=str(account_id),
            amount=payload.amount,
            datetime_start=datetime.now(timezone.utc),
            type=TransactionType.SAVINGS_DEPOSIT,
            name="Пополнение счета",
        )
    )

    return {"message": "Счет успешно пополнен"}


@router.post("/{account_id}/withdraw", status_code=status.HTTP_202_ACCEPTED)
async def withdraw_from_savings_account(
    account_id: UUID,
    payload: SavingsAccountOperationRequest,
    current_user: CurrentUser,
    session: SessionDep,
) -> dict:
    """
    Снять средства с накопительного счета на дебетовую карту

    Args:
        account_id: Уникальный идентификатор накопительного счета
        payload: Сумма снятия в копейках (должна быть больше 0)
        current_user: Текущий авторизованный пользователь
        session: Сессия базы данных

    Returns:
        dict: Сообщение об успешном снятии

    Raises:
        HTTPException: 404 если счет не найден или не принадлежит пользователю
        HTTPException: 400 если недостаточно средств на счете
    """

    user_item_repository = UserItemRepository(session)
    transaction_repository = TransactionRepository(session)
    item_repository = ItemRepository(session)

    # Проверяем существование счета
    account = await user_item_repository.get_by_id(account_id)
    if not account or account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Накопительный счет не найден",
        )

    # Проверяем достаточность средств
    if account.amount < payload.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недостаточно средств на счете",
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

    # Снимаем с накопительного счета
    await user_item_repository.update_amount(
        account_id, account.amount - payload.amount
    )

    # Пополняем дебетовый счет
    await user_item_repository.update_amount(
        debet_item.id, debet_item.amount + payload.amount
    )

    # Создаем транзакцию снятия с накопительного счета
    await transaction_repository.create(
        TransactionCreate(
            user_id=current_user.id,
            instrument_id=str(account_id),
            amount=-payload.amount,  # Отрицательная сумма для снятия
            datetime_start=datetime.now(timezone.utc),
            type=TransactionType.SAVINGS_WITHDRAWAL,
            name="Снятие со счета",
        )
    )

    # Создаем транзакцию пополнения дебетового счета
    await transaction_repository.create(
        TransactionCreate(
            user_id=current_user.id,
            instrument_id=str(debet_item.id),
            amount=payload.amount,
            datetime_start=datetime.now(timezone.utc),
            type=TransactionType.BANK,
            name="Перевод с накопительного счета",
        )
    )

    return {"message": "Средства успешно сняты со счета"}


@router.post("/{account_id}/close", response_model=SavingsAccountCloseResponse)
async def close_savings_account(
    account_id: UUID,
    current_user: CurrentUser,
    session: SessionDep,
) -> SavingsAccountCloseResponse:
    """
    Закрыть накопительный счет и перевести остаток на дебетовый счет

    Args:
        account_id: Уникальный идентификатор накопительного счета
        current_user: Текущий авторизованный пользователь
        session: Сессия базы данных

    Returns:
        SavingsAccountCloseResponse: ID закрытого счета и переведенная сумма

    Raises:
        HTTPException: 404 если счет не найден или не принадлежит пользователю
    """

    user_item_repository = UserItemRepository(session)
    transaction_repository = TransactionRepository(session)

    # Проверяем существование счета
    account = await user_item_repository.get_by_id(account_id)
    if not account or account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Накопительный счет не найден",
        )

    transferred_amount = account.amount

    # Если есть остаток, создаем транзакцию закрытия
    if transferred_amount > 0:
        await transaction_repository.create(
            TransactionCreate(
                user_id=current_user.id,
                instrument_id=str(account_id),
                amount=-transferred_amount,
                datetime_start=datetime.now(timezone.utc),
                type=TransactionType.SAVINGS_WITHDRAWAL,
                name="Закрытие счета",
            )
        )

    # Помечаем счет как закрытый (обнуляем баланс)
    await user_item_repository.update_amount(account_id, 0)

    return SavingsAccountCloseResponse(
        account_id=account_id,
        transferred_amount=transferred_amount,
    )


@router.get(
    "/{account_id}/transactions", response_model=SavingsAccountTransactionsResponse
)
async def list_savings_account_transactions(
    account_id: UUID,
    current_user: CurrentUser,
    session: SessionDep,
) -> SavingsAccountTransactionsResponse:
    """
    Получить список транзакций по накопительному счету

    Args:
        account_id: Уникальный идентификатор накопительного счета
        current_user: Текущий авторизованный пользователь
        session: Сессия базы данных

    Returns:
        SavingsAccountTransactionsResponse: Список транзакций с названием, суммой и датой

    Note:
        Исключаются транзакции с нулевой суммой

    Raises:
        HTTPException: 404 если счет не найден или не принадлежит пользователю
    """

    user_item_repository = UserItemRepository(session)
    transaction_repository = TransactionRepository(session)

    # Проверяем существование счета
    account = await user_item_repository.get_by_id(account_id)
    if not account or account.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Накопительный счет не найден",
        )

    # Получаем транзакции по этому счету
    transactions = await transaction_repository.list_by_instrument_id(str(account_id))

    # Преобразуем в схему ответа, исключая транзакции с нулевой суммой
    savings_transactions = []
    for transaction in transactions:
        if transaction.amount != 0:  # Исключаем нулевые транзакции
            savings_transactions.append(
                SavingsAccountTransaction(
                    id=transaction.id,
                    name=transaction.name,
                    amount=transaction.amount,
                    datetime_start=transaction.datetime_start,
                )
            )

    return SavingsAccountTransactionsResponse(
        account_id=account_id,
        transactions=savings_transactions,
    )
