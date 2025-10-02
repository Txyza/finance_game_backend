"""add savings accounts and deposits catalog items

Revision ID: 3a78bcb5cd9a
Revises: 3d0725c3e181
Create Date: 2025-09-30 13:28:16.226393

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "3a78bcb5cd9a"
down_revision: Union[str, None] = "3d0725c3e181"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_ITEMS_DATA = [
    # Накопительные счета
    {
        "name": "savings_basic",
        "description": "Накопительный счет: базовая ставка",
        "price": 0,
        "type": "savings",
        "exclusive": False,
        "energy_max_boost": 0.0,
        "energy_recovery_boost": 0.0,
        "energy_shild_boost": 0.0,
        "image": None,
        "duration_seconds": 0,
        "metadata": {
            "account_type": "basic",
            "currency": "RUB",
        },
    },
    {
        "name": "savings_premium",
        "description": "Накопительный счет Premium: повышенная ставка",
        "price": 0,
        "type": "savings",
        "exclusive": False,
        "energy_max_boost": 0.0,
        "energy_recovery_boost": 0.0,
        "energy_shild_boost": 0.0,
        "image": None,
        "duration_seconds": 0,
        "metadata": {
            "account_type": "premium",
            "currency": "RUB",
        },
    },
    # Депозитные продукты
    {
        "name": "deposit_kopit",
        "description": "Вклад 'Копить': классический срочный вклад с гарантированной доходностью",
        "price": 0,
        "type": "deposit",
        "exclusive": False,
        "energy_max_boost": 0.0,
        "energy_recovery_boost": 0.0,
        "energy_shild_boost": 0.0,
        "image": None,
        "duration_seconds": 0,
        "metadata": {
            "min_amount": 1500000,  # 15000 рублей в копейках
            "max_term_days": 15,  # 15 дней максимум
            "early_closure_penalty": True,
            "currency": "RUB",
            "product_type": "standard",
        },
    },
    {
        "name": "deposit_v_pluse",
        "description": "Вклад 'В Плюсе': премиальный вклад с повышенной ставкой и льготными условиями",
        "price": 0,
        "type": "deposit",
        "exclusive": False,
        "energy_max_boost": 0.0,
        "energy_recovery_boost": 0.0,
        "energy_shild_boost": 0.0,
        "image": None,
        "duration_seconds": 0,
        "metadata": {
            "min_amount": 1500000,  # 15000 рублей в копейках
            "max_term_days": 15,  # 15 дня максимум
            "early_closure_penalty": True,
            "currency": "RUB",
            "product_type": "premium",
        },
    },
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


def downgrade() -> None:
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
