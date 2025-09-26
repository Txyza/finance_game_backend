import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.schemas.transaction import TransactionType

if TYPE_CHECKING:
    from .user import User


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    instrument_id: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    datetime_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    datetime_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType, name="transaction_type"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="transactions")
