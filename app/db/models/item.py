from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.schemas.item import ItemType

if TYPE_CHECKING:
    from .user_item import UserItem


class Item(Base):
    __tablename__ = "items"

    name: Mapped[str] = mapped_column(String(255), primary_key=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[ItemType] = mapped_column(
        Enum(
            ItemType,
            name="item_type",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    exclusive: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    energy_max_boost: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    energy_recovery_boost: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    energy_shild_boost: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    image: Mapped[str | None] = mapped_column(Text, nullable=True)

    user_items: Mapped[list["UserItem"]] = relationship(
        "UserItem",
        back_populates="item",
        cascade="all, delete-orphan",
    )
