from typing import ClassVar

from app.schemas import WorkRead


class InMemoryWorkRepository:
    """Static list of arcade activities available in the game."""

    _WORKS: ClassVar[list[WorkRead]] = [
        WorkRead(
            name="2048",
            description="Собери плитки в легендарной головоломке и заработай деньги",
            base_energy=15,
            max_amount=5_000,
        ),
        WorkRead(
            name="memory",
            description="Проверь свою память, открывая пары карточек за ограниченное время",
            base_energy=10,
            max_amount=3_500,
        ),
    ]

    async def list_many(self) -> list[WorkRead]:
        return list(self._WORKS)

    async def get(self, name: str) -> WorkRead | None:
        for work in self._WORKS:
            if work.name == name:
                return work
        return None
