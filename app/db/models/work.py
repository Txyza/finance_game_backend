from sqlalchemy import Integer, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Work(Base):
    __tablename__ = "works"

    name: Mapped[str] = mapped_column(String(2048), primary_key=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    base_energy: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    max_amount: Mapped[int] = mapped_column(Integer, nullable=False)
