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
        "description": "Умная дебетовая карта Мир",
        "price": 0,
        "type": "debet",
        "exclusive": True,
        "energy_max_boost": 0.0,
        "energy_recovery_boost": 0.0,
        "energy_shild_boost": 0.0,
        "image": None,
        "duration_seconds": 2_147_483_647,
    },
    {
        "name": "supreme_mir",
        "description": "Премиальная карта Mir Supreme",
        "price": 0,
        "type": "debet",
        "exclusive": True,
        "energy_max_boost": 0.0,
        "energy_recovery_boost": 0.0,
        "energy_shild_boost": 0.0,
        "image": None,
        "duration_seconds": 2_147_483_647,
    },
    {
        "name": "energy_drink",
        "description": "Энергетический напиток для быстрого восстановления сил",
        "price": 150,
        "type": "finance",
        "exclusive": False,
        "energy_max_boost": 0.0,
        "energy_recovery_boost": 5.0,
        "energy_shild_boost": 0.0,
        "image": None,
        "duration_seconds": 3600,
    },
    {
        "name": "tactical_planner",
        "description": "Тактический планировщик увеличивает максимум энергии",
        "price": 1200,
        "type": "permanent",
        "exclusive": True,
        "energy_max_boost": 10.0,
        "energy_recovery_boost": 0.0,
        "energy_shild_boost": 0.0,
        "image": None,
        "duration_seconds": 3600,
    },
    {
        "name": "risk_shield",
        "description": "Щит от рисков снижает потери энергии после событий",
        "price": 800,
        "type": "finance",
        "exclusive": False,
        "energy_max_boost": 0.0,
        "energy_recovery_boost": 0.0,
        "energy_shild_boost": 0.15,
        "image": None,
        "duration_seconds": 3600,
    },
]

_WORKS_DATA = [
    {
        "name": "2048",
        "description": "Собери плитки в легендарной головоломке и заработай деньги",
        "base_energy": 15,
        "max_amount": 5_000,
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
        "name": "daily_login",
        "description": "Войдите в игру сегодня",
        "type": "daely",
        "reward": 100,
        "reward_type": "money",
        "progress_max_points": 1,
    },
    {
        "name": "daily_energy_drink",
        "description": "Используйте энергетический напиток",
        "type": "daely",
        "reward": 50,
        "reward_type": "money",
        "progress_max_points": 1,
    },
    {
        "name": "daily_work_session",
        "description": "Начните хотя бы одну рабочую сессию",
        "type": "daely",
        "reward": 120,
        "reward_type": "money",
        "progress_max_points": 1,
    },
    {
        "name": "daily_budget_check",
        "description": "Пополните свой счёт минимум на 500 единиц",
        "type": "daely",
        "reward": 80,
        "reward_type": "money",
        "progress_max_points": 1,
    },
    {
        "name": "daily_risk_shield",
        "description": "Активируйте защиту от рисков",
        "type": "daely",
        "reward": 30,
        "reward_type": "exp",
        "progress_max_points": 1,
    },
    {
        "name": "daily_deal_hunter",
        "description": "Совершите три мини-сделки за день",
        "type": "daely",
        "reward": 150,
        "reward_type": "money",
        "progress_max_points": 3,
    },
    {
        "name": "daily_training",
        "description": "Улучшите навык в любой мини-игре",
        "type": "daely",
        "reward": 40,
        "reward_type": "exp",
        "progress_max_points": 1,
    },
    {
        "name": "daily_social_bonus",
        "description": "Поделитесь достижением с друзьями",
        "type": "daely",
        "reward": 70,
        "reward_type": "money",
        "progress_max_points": 1,
    },
    {
        "name": "daily_planner_update",
        "description": "Обновите цели в тактическом планировщике",
        "type": "daely",
        "reward": 60,
        "reward_type": "exp",
        "progress_max_points": 1,
    },
    # Weekly tasks
    {
        "name": "weekly_strategy",
        "description": "Завершите пять рабочих сессий за неделю",
        "type": "weakly",
        "reward": 500,
        "reward_type": "money",
        "progress_max_points": 5,
    },
    {
        "name": "weekly_investor",
        "description": "Заработайте 5 000 единиц за неделю",
        "type": "weakly",
        "reward": 800,
        "reward_type": "money",
        "progress_max_points": 5000,
    },
    {
        "name": "weekly_collector",
        "description": "Соберите все ежедневные награды недели",
        "type": "weakly",
        "reward": 300,
        "reward_type": "exp",
        "progress_max_points": 3 * 7,
    },
    {
        "name": "weekly_teamwork",
        "description": "Помогите трём друзьям завершить задания",
        "type": "weakly",
        "reward": 600,
        "reward_type": "money",
        "progress_max_points": 3,
    },
    {
        "name": "weekly_savings",
        "description": "Сохраните 2 000 единиц на дебетовом счёте",
        "type": "weakly",
        "reward": 450,
        "reward_type": "money",
        "progress_max_points": 2000,
    },
    {
        "name": "weekly_market_guru",
        "description": "Проведите десять успешных сделок",
        "type": "weakly",
        "reward": 900,
        "reward_type": "exp",
        "progress_max_points": 10,
    },
    {
        "name": "weekly_resourceful",
        "description": "Используйте пять бустеров энергии",
        "type": "weakly",
        "reward": 400,
        "reward_type": "money",
        "progress_max_points": 5,
    },
    {
        "name": "weekly_planner_master",
        "description": "Завершите все пункты планировщика недели",
        "type": "weakly",
        "reward": 700,
        "reward_type": "exp",
        "progress_max_points": 4,
    },
    {
        "name": "weekly_event_runner",
        "description": "Участвуйте в трёх событиях недели",
        "type": "weakly",
        "reward": 550,
        "reward_type": "money",
        "progress_max_points": 3,
    },
    # Quest tasks
    {
        "name": "quest_collector",
        "description": "Соберите обе дебетовые карты",
        "type": "quest",
        "reward": 1_000,
        "reward_type": "exp",
        "progress_max_points": 2,
    },
    {
        "name": "quest_energy_tycoon",
        "description": "Увеличьте максимум энергии до 150",
        "type": "quest",
        "reward": 1_500,
        "reward_type": "money",
        "progress_max_points": 1,
    },
    {
        "name": "quest_market_legends",
        "description": "Совершите 100 успешных сделок",
        "type": "quest",
        "reward": 2_000,
        "reward_type": "exp",
        "progress_max_points": 100,
    },
    {
        "name": "quest_storyline",
        "description": "Пройдите все миссии сюжетной ветки",
        "type": "quest",
        "reward": 2_500,
        "reward_type": "exp",
        "progress_max_points": 5,
    },
    {
        "name": "quest_mentor",
        "description": "Обучите пятерых новичков",
        "type": "quest",
        "reward": 1_800,
        "reward_type": "money",
        "progress_max_points": 5,
    },
    {
        "name": "quest_world_tour",
        "description": "Откройте все города на карте",
        "type": "quest",
        "reward": 2_200,
        "reward_type": "exp",
        "progress_max_points": 6,
    },
    {
        "name": "quest_ultimate_collection",
        "description": "Соберите 20 уникальных предметов",
        "type": "quest",
        "reward": 3_000,
        "reward_type": "money",
        "progress_max_points": 20,
    },
    {
        "name": "quest_bank_innovator",
        "description": "Разблокируйте все банковские продукты",
        "type": "quest",
        "reward": 2_700,
        "reward_type": "exp",
        "progress_max_points": 4,
    },
    {
        "name": "quest_legend",
        "description": "Достигните максимального уровня опыта",
        "type": "quest",
        "reward": 5_000,
        "reward_type": "money",
        "progress_max_points": 1,
    },
]

_ITEM_TYPE = postgresql.ENUM(
    "finance", "permanent", "debet", name="item_type", create_type=False
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
