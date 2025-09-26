from typing import ClassVar

from app.schemas import ItemNames, ItemRead, ItemType


class InMemoryItemRepository:
    """Static catalogue of store items kept entirely in memory."""

    _ITEMS: ClassVar[list[ItemRead]] = [
        ItemRead(
            name=ItemNames.SMART_MIR.value,
            description="Умная дебетовая карта Мир",
            price=0,
            type=ItemType.DEBET,
            exclusive=True,
            energy_max_boost=0.0,
            energy_recovery_boost=0.0,
            energy_shild_boost=0.0,
            image=None,
        ),
        ItemRead(
            name=ItemNames.SUPREME_MIR.value,
            description="Премиальная карта Mir Supreme",
            price=0,
            type=ItemType.DEBET,
            exclusive=True,
            energy_max_boost=0.0,
            energy_recovery_boost=0.0,
            energy_shild_boost=0.0,
            image=None,
        ),
        ItemRead(
            name=ItemNames.ENERGY_DRINK.value,
            description="Энергетический напиток для быстрого восстановления сил",
            price=150,
            type=ItemType.FINANCE,
            exclusive=False,
            energy_max_boost=0.0,
            energy_recovery_boost=5.0,
            energy_shild_boost=0.0,
            image=None,
        ),
        ItemRead(
            name=ItemNames.TACTICAL_PLANNER.value,
            description="Тактический планировщик увеличивает максимум энергии",
            price=1200,
            type=ItemType.PERMANENT,
            exclusive=True,
            energy_max_boost=10.0,
            energy_recovery_boost=0.0,
            energy_shild_boost=0.0,
            image=None,
        ),
        ItemRead(
            name=ItemNames.RISK_SHIELD.value,
            description="Щит от рисков снижает потери энергии после событий",
            price=800,
            type=ItemType.FINANCE,
            exclusive=False,
            energy_max_boost=0.0,
            energy_recovery_boost=0.0,
            energy_shild_boost=0.15,
            image=None,
        ),
    ]

    async def list_many(self) -> list[ItemRead]:
        return list(self._ITEMS)

    async def get(self, name: str) -> ItemRead | None:
        for item in self._ITEMS:
            if item.name == name:
                return item
        return None
