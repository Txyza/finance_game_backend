import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from .task import Task
    from .user import User


class UserTask(Base):
    __tablename__ = "user_tasks"
    __table_args__ = (
        UniqueConstraint("user_id", "task_name", name="uix_user_task_user_task"),
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
    task_name: Mapped[str] = mapped_column(
        String(255), ForeignKey("tasks.name"), nullable=False
    )
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rewarded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    user: Mapped["User"] = relationship("User", back_populates="task_progress")
    task: Mapped["Task"] = relationship("Task", back_populates="user_tasks")
