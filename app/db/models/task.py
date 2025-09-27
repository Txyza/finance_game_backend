from typing import TYPE_CHECKING

from sqlalchemy import Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.schemas.task import RewardType, TaskType

if TYPE_CHECKING:
    from .user_task import UserTask


class Task(Base):
    __tablename__ = "tasks"

    name: Mapped[str] = mapped_column(String(255), primary_key=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[TaskType] = mapped_column(
        Enum(
            TaskType,
            name="task_type",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    reward: Mapped[int] = mapped_column(Integer, nullable=False)
    reward_type: Mapped[RewardType] = mapped_column(
        Enum(
            RewardType,
            name="reward_type",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    progress_max_points: Mapped[int] = mapped_column(Integer, nullable=False)

    user_tasks: Mapped[list["UserTask"]] = relationship(
        "UserTask",
        back_populates="task",
        cascade="all, delete-orphan",
    )
