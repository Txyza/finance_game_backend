from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, Tuple

from app.repositories import ItemRepository
from app.schemas import ItemRead, ItemType, UserItemRead

InventoryEntry = Tuple[UserItemRead, ItemRead]


async def attach_items(
    user_items: Iterable[UserItemRead],
    item_repository: ItemRepository,
) -> list[InventoryEntry]:
    results: list[InventoryEntry] = []
    now = datetime.now(timezone.utc)
    for user_item in user_items:
        if user_item.expaired_at is not None and user_item.expaired_at <= now:
            # Просроченные предметы не участвуют в расчётах.
            continue

        item = await item_repository.get(user_item.item_name)
        if item is None:
            continue
        if is_instant_item(item):
            # Моментальные предметы не должны быть привязаны к пользователю.
            continue
        results.append((user_item, item))
    return results


def find_primary_debet_item(
    inventory: Iterable[InventoryEntry],
) -> InventoryEntry | None:
    for entry in inventory:
        _, item = entry
        if item.type == ItemType.DEBET:
            return entry
    return None


def is_instant_item(item: ItemRead) -> bool:
    """Return True if the item acts instantly without being attached."""

    return item.type == ItemType.FINANCE and item.duration_seconds == 0
