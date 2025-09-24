import uuid
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, SmallInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from .item_user import ItemUser
    from .transaction import Transaction
    from .user_task import UserTask


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    energy: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    experience: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)

    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    items: Mapped[list["ItemUser"]] = relationship(
        "ItemUser",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    task_progress: Mapped[list["UserTask"]] = relationship(
        "UserTask",
        back_populates="user",
        cascade="all, delete-orphan",
    )
