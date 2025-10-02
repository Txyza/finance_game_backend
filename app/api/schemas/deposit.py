import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class InterestPaymentMethod(str, Enum):
    """Способ выплаты процентов"""

    AT_END = "at_end"  # В конце срока
    MONTHLY_CAPITALIZED = "monthly_capitalized"  # Ежемесячно с капитализацией
    MONTHLY_TO_ACCOUNT = "monthly_to_account"  # Ежемесячно на счет


class DepositListItem(BaseModel):
    """Элемент списка вкладов"""

    id: uuid.UUID
    deposit_name: str = Field(description="Название вклада")
    account_number: str = Field(description="Номер счета (до 6 цифр)")
    current_interest_rate: float = Field(ge=0, description="Текущая ставка по вкладу")
    balance: int = Field(ge=0, description="Баланс вклада в копейках")
    days_remaining: int = Field(ge=0, description="Остался срок вклада в днях")


class DepositListResponse(BaseModel):
    """Ответ со списком вкладов"""

    deposits: list[DepositListItem]


class DepositDetail(BaseModel):
    """Детальная карточка вклада"""

    id: uuid.UUID
    deposit_name: str = Field(description="Название вклада")
    account_number: str = Field(description="Номер счета (до 6 цифр)")
    current_interest_rate: float = Field(ge=0, description="Текущая ставка по вкладу")
    balance: int = Field(ge=0, description="Баланс вклада в копейках")
    opened_at: datetime = Field(description="Дата открытия вклада")
    expires_at: datetime = Field(description="Дата окончания срока вклада")
    days_remaining: int = Field(ge=0, description="Остался срок вклада в днях")
    interest_payment_method: InterestPaymentMethod = Field(
        description="Способ выплаты процентов"
    )


class DepositCreateRequest(BaseModel):
    """Запрос на создание вклада"""

    deposit_name: str = Field(max_length=255, description="Название вклада")
    amount: int = Field(gt=0, description="Сумма вклада в копейках")
    term_days: int = Field(
        ge=1, le=1095, description="Срок вклада в днях (максимум 3 года)"
    )
    interest_rate: float = Field(
        gt=0, le=25.0, description="Процентная ставка (не более 25%)"
    )
    interest_payment_method: InterestPaymentMethod = Field(
        description="Способ выплаты процентов"
    )

    @field_validator("interest_rate")
    @classmethod
    def validate_interest_rate(cls, v: float) -> float:
        """Проверяем, что ставка не превышает ключевую ставку (условно 21%)"""
        key_rate = 21.0  # Ключевая ставка ЦБ РФ (можно вынести в конфиг)
        if v > key_rate:
            raise ValueError(
                f"Процентная ставка не может превышать ключевую ставку {key_rate}%"
            )
        return v


class DepositCreateResponse(BaseModel):
    """Ответ на создание вклада"""

    deposit_id: uuid.UUID
    account_number: str
    expires_at: datetime


class DepositCloseResponse(BaseModel):
    """Ответ на досрочное закрытие вклада"""

    deposit_id: uuid.UUID
    transferred_amount: int = Field(ge=0, description="Переведенная сумма в копейках")
    penalty_applied: bool = Field(
        description="Была ли применена пеня за досрочное закрытие"
    )
    penalty_message: str = Field(description="Сообщение о пене")


class DepositTransaction(BaseModel):
    """Транзакция по вкладу"""

    id: uuid.UUID
    name: str = Field(
        description="Название операции (открытие, проценты, досрочное закрытие)"
    )
    amount: int = Field(description="Сумма в копейках (не может быть 0)")
    datetime_start: datetime = Field(description="Дата операции")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class DepositTransactionsResponse(BaseModel):
    """Ответ со списком транзакций по вкладу"""

    deposit_id: uuid.UUID
    transactions: list[DepositTransaction]
