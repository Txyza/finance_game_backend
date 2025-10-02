import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class SavingsAccountListItem(BaseModel):
    """Элемент списка накопительных счетов"""

    id: uuid.UUID
    account_name: str = Field(description="Название счета (Basic, Premium)")
    account_number: str = Field(description="Номер счета (до 6 цифр)")
    current_interest_rate: float = Field(ge=0, description="Текущая ставка по счету")
    balance: int = Field(ge=0, description="Баланс счета в копейках")


class SavingsAccountListResponse(BaseModel):
    """Ответ со списком накопительных счетов"""

    accounts: list[SavingsAccountListItem]


class SavingsAccountDetail(BaseModel):
    """Детальная карточка накопительного счета"""

    id: uuid.UUID
    account_name: str = Field(description="Название счета (Basic, Premium)")
    account_number: str = Field(description="Номер счета (до 6 цифр)")
    current_interest_rate: float = Field(ge=0, description="Текущая ставка по счету")
    balance: int = Field(ge=0, description="Баланс счета в копейках")
    opened_at: datetime = Field(description="Дата открытия счета")
    expires_at: datetime | None = Field(
        default=None, description="Дата истечения срока действия"
    )


class SavingsAccountCreateRequest(BaseModel):
    """Запрос на создание накопительного счета"""

    account_type: str = Field(description="Тип накопительного счета")
    initial_deposit: int = Field(
        default=0, ge=0, description="Начальный депозит в копейках"
    )


class SavingsAccountCreateResponse(BaseModel):
    """Ответ на создание накопительного счета"""

    account_id: uuid.UUID
    account_number: str


class SavingsAccountOperationRequest(BaseModel):
    """Запрос на операцию по счету (пополнение/снятие)"""

    amount: int = Field(gt=0, description="Сумма операции в копейках")


class SavingsAccountCloseResponse(BaseModel):
    """Ответ на закрытие накопительного счета"""

    account_id: uuid.UUID
    transferred_amount: int = Field(ge=0, description="Переведенная сумма в копейках")


class SavingsAccountTransaction(BaseModel):
    """Транзакция по накопительному счету"""

    id: uuid.UUID
    name: str = Field(description="Название операции (пополнение, снятие, проценты)")
    amount: int = Field(description="Сумма в копейках (не может быть 0)")
    datetime_start: datetime = Field(description="Дата операции")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class SavingsAccountTransactionsResponse(BaseModel):
    """Ответ со списком транзакций по счету"""

    account_id: uuid.UUID
    transactions: list[SavingsAccountTransaction]


class SavingsAvailableProduct(BaseModel):
    """Карточка доступного типа накопительного счёта с текущей ставкой."""

    account_type: str = Field(description="Тип счета (basic, premium)")
    account_name: str = Field(description="Отображаемое имя счёта")
    interest_rate: float = Field(ge=0, description="Текущая ставка в процентах годовых")


class SavingsAvailableResponse(BaseModel):
    """Ответ со списком доступных накопительных продуктов и их текущих ставок."""

    products: list[SavingsAvailableProduct]
