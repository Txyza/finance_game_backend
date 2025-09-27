from __future__ import annotations

from typing import Iterable, Tuple

from app.repositories import ItemRepository
from app.schemas import ItemRead, ItemType, UserItemRead

InventoryEntry = Tuple[UserItemRead, ItemRead]


async def attach_items(
    user_items: Iterable[UserItemRead],
    item_repository: ItemRepository,
) -> list[InventoryEntry]:
    results: list[InventoryEntry] = []
    for user_item in user_items:
        item = await item_repository.get(user_item.item_name)
        if item is None:
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
