"""Normalize enum values to match application models

Revision ID: 6d76331c4fa2
Revises: 0675c7511f6d
Create Date: 2025-09-27 16:25:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6d76331c4fa2"
down_revision: Union[str, None] = "0675c7511f6d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_UPGRADE_DEFINITIONS = {
    "item_type": {
        "values": ("finance", "permanent", "debet"),
        "table": "items",
        "column": "type",
        "transform": "LOWER",
    },
    "task_type": {
        "values": ("daely", "weakly", "quest"),
        "table": "tasks",
        "column": "type",
        "transform": "LOWER",
    },
    "reward_type": {
        "values": ("money", "exp"),
        "table": "tasks",
        "column": "reward_type",
        "transform": "LOWER",
    },
    "transaction_type": {
        "values": ("bank", "event", "work"),
        "table": "transactions",
        "column": "type",
        "transform": "LOWER",
    },
}

_DOWNGRADE_DEFINITIONS = {
    "item_type": {
        "values": ("FINANCE", "PERMANENT"),
        "table": "items",
        "column": "type",
        "transform": "UPPER",
        "cleanup": "DELETE FROM items WHERE type = 'debet'",
    },
    "task_type": {
        "values": ("DAELY", "WEAKLY", "QUEST"),
        "table": "tasks",
        "column": "type",
        "transform": "UPPER",
    },
    "reward_type": {
        "values": ("MONEY", "EXP"),
        "table": "tasks",
        "column": "reward_type",
        "transform": "UPPER",
    },
    "transaction_type": {
        "values": ("BANK", "EVENT", "WORK"),
        "table": "transactions",
        "column": "type",
        "transform": "UPPER",
    },
}


def _recreate_enum(
    *, enum_name: str, values: tuple[str, ...], table: str, column: str, transform: str
) -> None:
    values_sql = ", ".join(f"'{value}'" for value in values)
    with op.get_context().autocommit_block():
        op.execute(f"ALTER TYPE {enum_name} RENAME TO {enum_name}_old")
        op.execute(f"CREATE TYPE {enum_name} AS ENUM ({values_sql})")
        op.execute(
            f"ALTER TABLE {table} ALTER COLUMN {column} TYPE {enum_name} "
            f"USING {transform}({column}::text):: {enum_name}"
        )
        op.execute(f"DROP TYPE {enum_name}_old")


def upgrade() -> None:
    for enum_name, definition in _UPGRADE_DEFINITIONS.items():
        _recreate_enum(
            enum_name=enum_name,
            values=definition["values"],
            table=definition["table"],
            column=definition["column"],
            transform=definition["transform"],
        )


def downgrade() -> None:
    for enum_name, definition in _DOWNGRADE_DEFINITIONS.items():
        cleanup_sql = definition.get("cleanup")
        if cleanup_sql:
            with op.get_context().autocommit_block():
                op.execute(cleanup_sql)
        _recreate_enum(
            enum_name=enum_name,
            values=definition["values"],
            table=definition["table"],
            column=definition["column"],
            transform=definition["transform"],
        )
