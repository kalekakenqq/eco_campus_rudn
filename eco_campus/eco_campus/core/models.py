"""
Доменные модели данных приложения EcoCampus.

Все поля строго типизированы. Модели не зависят от фреймворков —
их можно использовать в любом слое приложения.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class WasteType(str, Enum):
    """Типы отходов, принимаемых в экопунктах кампуса РУДН."""

    PLASTIC = "plastic"
    PAPER = "paper"
    GLASS = "glass"
    METAL = "metal"
    TEXTILE = "textile"
    ELECTRONICS = "electronics"
    ORGANIC = "organic"
    MIXED = "mixed"

    @classmethod
    def labels(cls) -> dict["WasteType", str]:
        """Возвращает словарь с человекочитаемыми названиями типов."""
        return {
            cls.PLASTIC: "Пластик / ПЭТ-бутылки",
            cls.PAPER: "Бумага / Макулатура",
            cls.GLASS: "Стекло",
            cls.METAL: "Металл / Алюминиевые банки",
            cls.TEXTILE: "Текстиль",
            cls.ELECTRONICS: "Электроника / Батарейки",
            cls.ORGANIC: "Органика",
            cls.MIXED: "Смешанные отходы",
        }

    def label(self) -> str:
        """Возвращает человекочитаемое название типа."""
        return self.labels().get(self, self.value)


@dataclass(frozen=True)
class Coordinates:
    """Географические координаты точки на карте."""

    lat: float
    lon: float

    def __post_init__(self) -> None:
        if not (-90 <= self.lat <= 90):
            raise ValueError(f"Некорректная широта: {self.lat}")
        if not (-180 <= self.lon <= 180):
            raise ValueError(f"Некорректная долгота: {self.lon}")


@dataclass
class Container:
    """Контейнер для сбора отходов на территории кампуса."""

    container_id: str
    name: str
    location_name: str
    coordinates: Coordinates
    accepted_types: list[WasteType]
    working_hours: str = "08:00-22:00"
    is_active: bool = True
    description: str = ""

    def accepts(self, waste_type: WasteType) -> bool:
        """Проверяет, принимает ли контейнер данный тип отходов."""
        return waste_type in self.accepted_types


@dataclass
class RouteStep:
    """Один шаг навигационного маршрута."""

    from_node: str
    to_node: str
    distance_meters: float
    instruction: str


@dataclass
class Route:
    """Маршрут от текущей позиции пользователя до контейнера."""

    target_container: Container
    waste_type: WasteType
    steps: list[RouteStep] = field(default_factory=list)
    total_distance_meters: float = 0.0
    estimated_minutes: float = 0.0

    def summary(self) -> str:
        """Возвращает краткое текстовое описание маршрута."""
        if self.total_distance_meters < 1000:
            distance = f"{self.total_distance_meters:.0f} м"
        else:
            distance = f"{self.total_distance_meters / 1000:.1f} км"

        return (
            f"Контейнер: {self.target_container.name}\n"
            f"Принимает: {self.waste_type.label()}\n"
            f"Расстояние: {distance}\n"
            f"Примерно {self.estimated_minutes:.0f} мин пешком\n"
            f"Режим работы: {self.target_container.working_hours}"
        )


@dataclass
class UserLocation:
    """Текущая позиция пользователя в кампусе."""

    node_id: str
    display_name: str
    coordinates: Optional[Coordinates] = None


@dataclass
class ClassificationResult:
    """Результат классификации отходов по текстовому описанию."""

    waste_type: WasteType
    confidence: float
    matched_keywords: list[str]

    def is_confident(self, threshold: float = 0.5) -> bool:
        """Возвращает True, если уверенность классификации выше порога."""
        return self.confidence >= threshold
