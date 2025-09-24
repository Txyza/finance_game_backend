import uuid
from typing import Any, TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from .item import Item
    from .user import User


class ItemUser(Base):
    __tablename__ = "item_user"
    __table_args__ = (
        UniqueConstraint("user_id", "item_name", name="uix_item_user_user_item"),
    )

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
    item_name: Mapped[str] = mapped_column(
        String(255), ForeignKey("items.name"), nullable=False
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    user: Mapped["User"] = relationship("User", back_populates="items")
    item: Mapped["Item"] = relationship("Item", back_populates="user_items")
