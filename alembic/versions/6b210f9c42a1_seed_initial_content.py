"""seed initial content for catalog tables

Revision ID: 6b210f9c42a1
Revises: 35c5d88c55f1
Create Date: 2025-09-27 14:10:00.000000

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "6b210f9c42a1"
down_revision: Union[str, None] = "35c5d88c55f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_ITEMS_DATA = [
    {
        "name": "smart_mir",
        "description": "Умная карта Мир: базовая дебетовая карта",
        "price": 0,
        "type": "debet",
        "exclusive": True,
        "energy_max_boost": 0.0,
        "energy_recovery_boost": 0.0,
        "energy_shild_boost": 0.0,
        "image": None,
        "duration_seconds": 2_147_483_647,
        "metadata": {},
    },
    {
        "name": "supreme_mir",
        "description": "Премиальная карта Mir Supreme: расширенный доступ к финансам",
        "price": 0,
        "type": "debet",
        "exclusive": True,
        "energy_max_boost": 0.0,
        "energy_recovery_boost": 0.0,
        "energy_shild_boost": 0.0,
        "image": None,
        "duration_seconds": 2_147_483_647,
        "metadata": {},
    },
    {
        "name": "Энергетический шот",
        "description": "Энергетический шот мгновенно восстанавливает 50 единиц энергии",
        "price": 150,
        "type": "finance",
        "exclusive": False,
        "energy_max_boost": 0.0,
        "energy_recovery_boost": 50.0,
        "energy_shild_boost": 0.0,
        "image": None,
        "duration_seconds": 0,
        "metadata": {},
    },
    {
        "name": "Чип расширения батареи",
        "description": "Чип расширения батареи увеличивает максимум энергии на 20 единиц на 24 часа",
        "price": 1200,
        "type": "finance",
        "exclusive": False,
        "energy_max_boost": 20.0,
        "energy_recovery_boost": 0.0,
        "energy_shild_boost": 0.0,
        "image": None,
        "duration_seconds": 86_400,
        "metadata": {},
    },
    {
        "name": "Биостимулятор восстановления",
        "description": "Биостимулятор ускоряет восстановление энергии +10 ед./час на 6 часов",
        "price": 900,
        "type": "finance",
        "exclusive": False,
        "energy_max_boost": 0.0,
        "energy_recovery_boost": 10.0,
        "energy_shild_boost": 0.0,
        "image": None,
        "duration_seconds": 21_600,
        "metadata": {},
    },
    {
        "name": "Эмиттер защиты",
        "description": "Эмиттер защиты снижает потери энергии на 20% на 12 часов",
        "price": 800,
        "type": "finance",
        "exclusive": True,
        "energy_max_boost": 0.0,
        "energy_recovery_boost": 0.0,
        "energy_shild_boost": 0.2,
        "image": None,
        "duration_seconds": 43_200,
        "metadata": {},
    },
    {
        "name": "Аренда квартиры",
        "description": "Аренда комфортной квартиры на 3 дня",
        "price": 1500,
        "type": "rent",
        "exclusive": True,
        "energy_max_boost": 0.0,
        "energy_recovery_boost": 0.0,
        "energy_shild_boost": 0.0,
        "image": None,
        "duration_seconds": 259_200,
        "metadata": {},
    },
    {
        "name": "Накопительный счет базовый",
        "description": "Сберегательный продукт с фиксированной ставкой",
        "price": 0,
        "type": "savings",
        "exclusive": False,
        "energy_max_boost": 0.0,
        "energy_recovery_boost": 0.0,
        "energy_shild_boost": 0.0,
        "image": None,
        "duration_seconds": 0,
        "metadata": {
            "interest_rate": 0.075,
            "capitalization_period_days": 30,
            "currency": "RUB",
        },
    },
]

_WORKS_DATA = [
    {
        "name": "2048",
        "description": "Собери плитки в легендарной головоломке и заработай деньги",
        "base_energy": 15,
        "max_amount": 10_000,
    },
    {
        "name": "memory",
        "description": "Проверь свою память, открывая пары карточек за ограниченное время",
        "base_energy": 10,
        "max_amount": 3_500,
    },
]

_TASKS_DATA = [
    # Daily tasks
    {
        "name": "Энергетический напиток",
        "description": "Используйте энергетический напиток",
        "type": "daely",
        "reward": 50,
        "reward_type": "money",
        "progress_max_points": 1,
    },
    {
        "name": "Ежедневный бюджет",
        "description": "Пополните свой счёт минимум на 500 единиц",
        "type": "daely",
        "reward": 80,
        "reward_type": "money",
        "progress_max_points": 1,
    },
    {
        "name": "Покупаем защиту от рисков!",
        "description": "Активируйте защиту от рисков",
        "type": "daely",
        "reward": 30,
        "reward_type": "exp",
        "progress_max_points": 1,
    },
    # Weekly tasks
    {
        "name": "Недельный инвестор!",
        "description": "Заработайте 5 000 за неделю на инвестициях",
        "type": "weakly",
        "reward": 800,
        "reward_type": "exp",
        "progress_max_points": 5000,
    },
    {
        "name": "Сохраним деньги",
        "description": "Сохраните 2 000 единиц на дебетовом счёте",
        "type": "weakly",
        "reward": 450,
        "reward_type": "money",
        "progress_max_points": 2000,
    },
    {
        "name": "События недели",
        "description": "Участвуйте в двух событиях недели",
        "type": "weakly",
        "reward": 550,
        "reward_type": "money",
        "progress_max_points": 2,
    },
    # Quest tasks
    {
        "name": "Заработай свои первые деньги!",
        "description": "Заработайте 5 000 единиц",
        "type": "quest",
        "reward": 50,
        "reward_type": "exp",
        "progress_max_points": 5_000,
    },
    {
        "name": "Приступим к работе",
        "description": "Начните хотя бы одну рабочую сессию",
        "type": "quest",
        "reward": 50,
        "reward_type": "exp",
        "progress_max_points": 1,
    },
    {
        "name": "Работник недели",
        "description": "Начните хотя бы одну рабочую сессию",
        "type": "quest",
        "reward": 100,
        "reward_type": "exp",
        "progress_max_points": 4,
    }
]

_ITEM_TYPE = postgresql.ENUM(
    "finance",
    "permanent",
    "debet",
    "rent",
    "savings",
    "deposit",
    name="item_type",
    create_type=False,
)
_TASK_TYPE = postgresql.ENUM(
    "daely", "weakly", "quest", name="task_type", create_type=False
)
_REWARD_TYPE = postgresql.ENUM("money", "exp", name="reward_type", create_type=False)


def upgrade() -> None:
    items_table = sa.table(
        "items",
        sa.column("name", sa.String(length=255)),
        sa.column("description", sa.Text()),
        sa.column("price", sa.Integer()),
        sa.column("type", _ITEM_TYPE),
        sa.column("exclusive", sa.Boolean()),
        sa.column("energy_max_boost", sa.Float()),
        sa.column("energy_recovery_boost", sa.Float()),
        sa.column("energy_shild_boost", sa.Float()),
        sa.column("duration_seconds", sa.Integer()),
        sa.column("image", sa.Text()),
    )
    op.bulk_insert(items_table, _ITEMS_DATA)

    works_table = sa.table(
        "works",
        sa.column("name", sa.String(length=2048)),
        sa.column("description", sa.Text()),
        sa.column("base_energy", sa.SmallInteger()),
        sa.column("max_amount", sa.Integer()),
    )
    op.bulk_insert(works_table, _WORKS_DATA)

    tasks_table = sa.table(
        "tasks",
        sa.column("name", sa.String(length=255)),
        sa.column("description", sa.Text()),
        sa.column("type", _TASK_TYPE),
        sa.column("reward", sa.Integer()),
        sa.column("reward_type", _REWARD_TYPE),
        sa.column("progress_max_points", sa.Integer()),
    )
    op.bulk_insert(tasks_table, _TASKS_DATA)


def downgrade() -> None:
    for task in _TASKS_DATA:
        name = task["name"]
        op.execute(
            sa.text("DELETE FROM user_tasks WHERE task_name = :name").bindparams(
                name=name
            )
        )
        op.execute(
            sa.text("DELETE FROM tasks WHERE name = :name").bindparams(name=name)
        )

    for item in _ITEMS_DATA:
        name = item["name"]
        op.execute(
            sa.text("DELETE FROM user_item WHERE item_name = :name").bindparams(
                name=name
            )
        )
        op.execute(
            sa.text("DELETE FROM items WHERE name = :name").bindparams(name=name)
        )

    for work in _WORKS_DATA:
        name = work["name"]
        op.execute(
            sa.text("DELETE FROM works WHERE name = :name").bindparams(name=name)
        )
