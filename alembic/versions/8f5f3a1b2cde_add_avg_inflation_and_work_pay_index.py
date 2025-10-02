"""add avg_inflation world setting

Revision ID: 8f5f3a1b2cde
Revises: 3a78bcb5cd9a
Create Date: 2025-10-01 10:00:00.000000

"""

from __future__ import annotations

from typing import Sequence, Union

from decimal import Decimal

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8f5f3a1b2cde"
down_revision: Union[str, None] = "3a78bcb5cd9a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    settings = sa.table(
        "world_settings",
        sa.column("name", sa.String(length=255)),
        sa.column("value", sa.Numeric(10, 4)),
        sa.column("description", sa.Text()),
    )

    op.bulk_insert(
        settings,
        [
            {
                "name": "avg_inflation",
                "value": Decimal("10.5"),
                "description": "Среднегодовая инфляция. Используется для индексации оплаты работы",
            }
        ],
    )


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM world_settings WHERE name = 'avg_inflation'"))
