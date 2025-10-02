"""add world settings table

Revision ID: 3d0725c3e181
Revises: 6b210f9c42a1
Create Date: 2025-09-28 20:30:00.000000

"""

from __future__ import annotations

from typing import Sequence, Union

from decimal import Decimal

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "3d0725c3e181"
down_revision: Union[str, None] = "6b210f9c42a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "world_settings",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("value", sa.Numeric(10, 4), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("name"),
    )

    settings_table = sa.table(
        "world_settings",
        sa.column("name", sa.String(length=255)),
        sa.column("value", sa.Numeric(10, 4)),
        sa.column("description", sa.Text()),
    )

    op.bulk_insert(
        settings_table,
        [
            {
                "name": "key_rate",
                "value": Decimal("12.5"),
                "description": "Влияет на доходность активов и проценты по кредитам",
            },
            {
                "name": "inflation",
                "value": Decimal("10.5"),
                "description": "Влияет на стоимость активов и предметов",
            },
        ],
    )


def downgrade() -> None:
    op.drop_table("world_settings")
