import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class InstrumentType(str, Enum):
    """Тип банковского инструмента"""
    DEBIT_CARD = "debit_card"
    SAVINGS_ACCOUNT = "savings_account"
    DEPOSIT = "deposit"


class BankingInstrument(BaseModel):
    """Банковский инструмент пользователя"""
    id: uuid.UUID
    type: InstrumentType = Field(description="Тип инструмента")
    name: str = Field(description="Название инструмента")
    account_number: str = Field(description="Номер счета/карты")
    balance: int = Field(ge=0, description="Баланс в копейках")
    interest_rate: float | None = Field(default=None, ge=0, description="Процентная ставка (для вкладов и накоплений)")
    opened_at: datetime = Field(description="Дата открытия")
    expires_at: datetime | None = Field(default=None, description="Дата окончания (для вкладов)")
    days_remaining: int | None = Field(default=None, ge=0, description="Дней до окончания (для вкладов)")


class BankingInstrumentsResponse(BaseModel):
    """Ответ со списком банковских инструментов"""
    debit_cards: list[BankingInstrument] = Field(description="Дебетовые карты")
    savings_accounts: list[BankingInstrument] = Field(description="Накопительные счета")
    deposits: list[BankingInstrument] = Field(description="Вклады")
    total_balance: int = Field(ge=0, description="Общий баланс всех инструментов в копейках")