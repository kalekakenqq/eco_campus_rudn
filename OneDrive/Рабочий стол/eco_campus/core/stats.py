"""
Модуль статистики запросов EcoCampus.
"""

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime

from eco_campus.core.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class StatsService:
    """Сервис сбора и хранения статистики запросов."""

    total_routes: int = 0
    waste_type_counter: Counter = field(default_factory=Counter)
    location_counter: Counter = field(default_factory=Counter)
    started_at: datetime = field(default_factory=datetime.now)

    def record_route(self, waste_type: str, location: str) -> None:
        """Фиксирует новый запрос маршрута."""
        self.total_routes += 1
        self.waste_type_counter[waste_type] += 1
        self.location_counter[location] += 1
        logger.debug("Статистика обновлена: всего маршрутов %d", self.total_routes)

    def top_waste_types(self, n: int = 3) -> list[dict]:
        return [
            {"waste_type": wt, "count": count}
            for wt, count in self.waste_type_counter.most_common(n)
        ]

    def top_locations(self, n: int = 3) -> list[dict]:
        return [
            {"location": loc, "count": count}
            for loc, count in self.location_counter.most_common(n)
        ]

    def summary(self) -> dict:
        uptime = datetime.now() - self.started_at
        hours = int(uptime.total_seconds() // 3600)
        minutes = int((uptime.total_seconds() % 3600) // 60)
        return {
            "total_routes": self.total_routes,
            "uptime": f"{hours}ч {minutes}мин",
            "top_waste_types": self.top_waste_types(),
            "top_locations": self.top_locations(),
            "started_at": self.started_at.strftime("%d.%m.%Y %H:%M"),
        }


stats_service = StatsService()
