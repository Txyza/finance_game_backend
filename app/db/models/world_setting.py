from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class WorldSetting(Base):
    __tablename__ = "world_settings"

    name: Mapped[str] = mapped_column(String(255), primary_key=True)
    value: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
