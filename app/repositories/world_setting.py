from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import WorldSetting


class WorldSettingRepository:
    """Репозиторий для работы с мировыми настройками"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_value(self, name: str) -> Optional[float]:
        """
        Получить значение настройки по имени

        Args:
            name: Имя настройки

        Returns:
            float | None: Значение настройки или None если не найдено
        """
        stmt = select(WorldSetting.value).where(WorldSetting.name == name)
        result = await self._session.execute(stmt)
        value = result.scalar_one_or_none()
        return float(value) if value is not None else None

    async def set_value(
        self, name: str, value: float, description: Optional[str] = None
    ) -> bool:
        """
        Установить значение настройки

        Args:
            name: Имя настройки
            value: Новое значение
            description: Описание (обновляется только если передано)

        Returns:
            bool: True если обновлено, False если создано новое
        """
        # Ищем существующую настройку
        stmt = select(WorldSetting).where(WorldSetting.name == name)
        result = await self._session.execute(stmt)
        setting = result.scalar_one_or_none()

        if setting:
            # Обновляем существующую
            setting.value = Decimal(str(value))
            if description:
                setting.description = description
            await self._session.flush()
            return True
        else:
            # Создаем новую
            setting = WorldSetting(
                name=name,
                value=Decimal(str(value)),
                description=description or f"Автоматически созданная настройка: {name}",
            )
            self._session.add(setting)
            await self._session.flush()
            return False

    async def update_value(self, name: str, delta: float) -> Optional[float]:
        """
        Изменить значение настройки на дельту

        Args:
            name: Имя настройки
            delta: Изменение значения (может быть отрицательным)

        Returns:
            float | None: Новое значение или None если настройка не найдена
        """
        stmt = select(WorldSetting).where(WorldSetting.name == name)
        result = await self._session.execute(stmt)
        setting = result.scalar_one_or_none()

        if setting:
            new_value = float(setting.value) + delta
            setting.value = Decimal(str(new_value))
            await self._session.flush()
            return new_value
        return None

    async def get_key_rate(self) -> float:
        """
        Получить ключевую ставку ЦБ

        Returns:
            float: Ключевая ставка в процентах
        """
        value = await self.get_value("key_rate")
        return value if value is not None else 12.5  # Значение по умолчанию

    async def set_key_rate(self, rate: float) -> None:
        """
        Установить ключевую ставку ЦБ

        Args:
            rate: Новая ключевая ставка в процентах
        """
        await self.set_value(
            "key_rate",
            rate,
            "Ключевая ставка Центрального Банка. Влияет на доходность активов и проценты по кредитам",
        )

    async def get_inflation_rate(self) -> float:
        """
        Получить годовой уровень инфляции

        Returns:
            float: Уровень инфляции в процентах
        """
        value = await self.get_value("inflation")
        return value if value is not None else 10.5  # Значение по умолчанию

    async def set_inflation_rate(self, rate: float) -> None:
        """
        Установить годовой уровень инфляции

        Args:
            rate: Новый уровень инфляции в процентах
        """
        await self.set_value(
            "inflation",
            rate,
            "Годовой уровень инфляции. Влияет на стоимость активов и предметов",
        )

    async def get_average_inflation_rate(self) -> float:
        """Получить среднегодовую инфляцию для индексации выплат по работе."""
        value = await self.get_value("avg_inflation")
        if value is None:
            return await self.get_inflation_rate()
        return value

    async def set_average_inflation_rate(self, rate: float) -> None:
        """Установить среднегодовую инфляцию."""
        await self.set_value(
            "avg_inflation",
            rate,
            "Среднегодовая инфляция. Используется для индексации оплаты работы",
        )

    # ---- Среднегодовая инфляция как среднее 4 недель "года" (28 дней) ----
    async def update_average_inflation_with_weekly_sample(self, sample: float) -> float:
        """
        Обновить среднегодовую инфляцию, добавив новый недельный сэмпл.

        Механика:
        - "Год" = 28 дней => 4 недели. Храним 4 ячейки: inflation_week_1..4
        - Индекс текущей недели хранится в setting "inflation_week_index" (1..4)
        - При обновлении перезаписываем следующую ячейку по кругу и
          пересчитываем среднее по заполненным ячейкам.

        Returns:
            float: Новое среднее значение avg_inflation
        """
        # Текущий индекс
        week_idx_val = await self.get_value("inflation_week_index")
        week_idx = int(week_idx_val) if week_idx_val is not None else 0
        next_idx = (week_idx % 4) + 1

        # Записываем сэмпл в соответствующую ячейку
        await self.set_value(
            f"inflation_week_{next_idx}",
            sample,
            f"Недельный сэмпл инфляции #{next_idx}",
        )
        await self.set_value(
            "inflation_week_index", float(next_idx), "Текущий индекс недели (1..4)"
        )

        # Читаем доступные ячейки и считаем среднее
        values: list[float] = []
        for i in range(1, 5):
            v = await self.get_value(f"inflation_week_{i}")
            if v is not None:
                values.append(v)

        avg = sample if not values else sum(values) / len(values)
        await self.set_average_inflation_rate(avg)
        return avg
