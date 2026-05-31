"""
Иерархия исключений для бизнес-логики EcoCampus.

Все исключения наследуются от EcoCampusError, что позволяет
перехватывать любую ошибку приложения одним except-блоком.
"""


class EcoCampusError(Exception):
    """Базовое исключение приложения."""

    def __init__(self, message: str, code: str = "ECO_ERROR") -> None:
        super().__init__(message)
        self.message = message
        self.code = code

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(code={self.code!r}, message={self.message!r})"


class RoutingError(EcoCampusError):
    """Ошибки при построении маршрута."""


class LocationNotFoundError(RoutingError):
    """Указанная локация не найдена на карте кампуса."""

    def __init__(self, location: str) -> None:
        super().__init__(
            message=f"Локация не найдена: {location!r}",
            code="LOCATION_NOT_FOUND",
        )
        self.location = location


class NoRouteError(RoutingError):
    """Маршрут между двумя точками не существует."""

    def __init__(self, source: str, target: str) -> None:
        super().__init__(
            message=f"Маршрут между {source!r} и {target!r} недоступен",
            code="NO_ROUTE",
        )
        self.source = source
        self.target = target


class DataError(EcoCampusError):
    """Ошибки при работе с данными."""


class ContainerNotFoundError(DataError):
    """Контейнер указанного типа отходов не найден."""

    def __init__(self, waste_type: str) -> None:
        super().__init__(
            message=f"Контейнер для '{waste_type}' не найден в базе",
            code="CONTAINER_NOT_FOUND",
        )
        self.waste_type = waste_type


class InvalidWasteTypeError(DataError):
    """Передан неизвестный тип отходов."""

    def __init__(self, waste_type: str) -> None:
        super().__init__(
            message=f"Неизвестный тип отходов: {waste_type!r}",
            code="INVALID_WASTE_TYPE",
        )
        self.waste_type = waste_type


class ClassificationError(EcoCampusError):
    """Ошибка классификации типа отходов."""

    def __init__(self, text: str) -> None:
        super().__init__(
            message=f"Не удалось определить тип отходов по тексту: {text!r}",
            code="CLASSIFICATION_ERROR",
        )
        self.text = text


class ConfigError(EcoCampusError):
    """Ошибки конфигурации приложения."""
