"""
Движок маршрутизации по кампусу РУДН.

Строит взвешенный граф кампуса и находит оптимальный маршрут
от текущей позиции пользователя до ближайшего подходящего
контейнера с помощью алгоритма Дейкстры (библиотека NetworkX).

Принцип Graceful Degradation: если запись о контейнере содержит
ошибочный узел графа, она пропускается без падения системы.
"""

import networkx as nx

from eco_campus.core.exceptions import (
    ContainerNotFoundError,
    LocationNotFoundError,
    NoRouteError,
)
from eco_campus.core.logger import setup_logger
from eco_campus.core.models import Container, Route, RouteStep, UserLocation, WasteType
from eco_campus.data.campus_data import CAMPUS_EDGES, CAMPUS_NODES, CONTAINERS

logger = setup_logger(__name__)

WALKING_SPEED_M_PER_MIN: float = 80.0


class CampusRouter:
    """
    Сервис маршрутизации по экопунктам кампуса.

    Граф строится один раз при инициализации и переиспользуется
    для всех запросов. Узлы — ключевые точки кампуса, рёбра —
    пешеходные пути с весами в метрах.
    """

    def __init__(self) -> None:
        self._graph: nx.Graph = nx.Graph()
        self._containers: list[Container] = list(CONTAINERS)
        self._nodes: dict[str, dict] = CAMPUS_NODES
        self._build_graph()
        logger.info(
            "CampusRouter инициализирован: %d узлов, %d рёбер, %d контейнеров",
            self._graph.number_of_nodes(),
            self._graph.number_of_edges(),
            len(self._containers),
        )

    def _build_graph(self) -> None:
        """Строит граф кампуса из узлов и рёбер."""
        for node_id, data in self._nodes.items():
            self._graph.add_node(node_id, **data)
        for u, v, weight in CAMPUS_EDGES:
            self._graph.add_edge(u, v, weight=weight)
        logger.debug("Граф кампуса построен")

    def get_locations(self) -> list[UserLocation]:
        """Возвращает список всех доступных локаций кампуса."""
        return [
            UserLocation(
                node_id=node_id,
                display_name=data["display"],
                coordinates=data.get("coords"),
            )
            for node_id, data in self._nodes.items()
        ]

    def find_containers(self, waste_type: WasteType) -> list[Container]:
        """
        Возвращает активные контейнеры, принимающие данный тип отходов.

        Args:
            waste_type: Тип отходов для поиска.

        Returns:
            Список подходящих контейнеров.

        Raises:
            ContainerNotFoundError: Если ни одного контейнера не найдено.
        """
        results = [
            c for c in self._containers
            if c.is_active and c.accepts(waste_type)
        ]
        if not results:
            logger.warning("Контейнеры для '%s' не найдены", waste_type.value)
            raise ContainerNotFoundError(waste_type.label())
        return results

    def find_nearest_route(
        self,
        from_location: str,
        waste_type: WasteType,
    ) -> Route:
        """
        Находит маршрут до ближайшего контейнера нужного типа.

        Перебирает все подходящие контейнеры и выбирает тот,
        путь до которого минимален по суммарному расстоянию.

        Args:
            from_location: Идентификатор стартового узла.
            waste_type: Тип отходов.

        Returns:
            Объект Route с пошаговым маршрутом.

        Raises:
            LocationNotFoundError: Если стартовая точка не найдена.
            ContainerNotFoundError: Если нет контейнеров для типа.
            NoRouteError: Если маршрут недостижим.
        """
        if from_location not in self._graph:
            logger.error("Неизвестная локация: '%s'", from_location)
            raise LocationNotFoundError(from_location)

        candidates = self.find_containers(waste_type)

        best_route: Route | None = None
        best_distance = float("inf")

        for container in candidates:
            target_node = container.location_name

            if target_node not in self._graph:
                logger.warning(
                    "Контейнер '%s' ссылается на несуществующий узел '%s', пропускается",
                    container.container_id,
                    target_node,
                )
                continue

            try:
                path: list[str] = nx.dijkstra_path(
                    self._graph, from_location, target_node, weight="weight"
                )
                distance: float = nx.dijkstra_path_length(
                    self._graph, from_location, target_node, weight="weight"
                )
            except nx.NetworkXNoPath:
                logger.debug(
                    "Нет пути от '%s' до '%s'", from_location, target_node
                )
                continue
            except nx.NodeNotFound as exc:
                logger.warning("Узел не найден при маршрутизации: %s", exc)
                continue

            if distance < best_distance:
                best_distance = distance
                best_route = Route(
                    target_container=container,
                    waste_type=waste_type,
                    steps=self._build_steps(path),
                    total_distance_meters=distance,
                    estimated_minutes=distance / WALKING_SPEED_M_PER_MIN,
                )

        if best_route is None:
            raise NoRouteError(from_location, waste_type.value)

        logger.info(
            "Маршрут найден: '%s' -> '%s' (%.0f м)",
            from_location,
            best_route.target_container.name,
            best_route.total_distance_meters,
        )
        return best_route

    def _build_steps(self, path: list[str]) -> list[RouteStep]:
        """Преобразует список узлов пути в читаемые шаги маршрута."""
        steps: list[RouteStep] = []
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            distance = self._graph[u][v]["weight"]
            from_name = self._nodes.get(u, {}).get("display", u)
            to_name = self._nodes.get(v, {}).get("display", v)
            steps.append(RouteStep(
                from_node=u,
                to_node=v,
                distance_meters=distance,
                instruction=f"Идите от '{from_name}' к '{to_name}' (около {distance:.0f} м)",
            ))
        return steps

    def all_containers(self) -> list[Container]:
        """Возвращает все контейнеры кампуса."""
        return list(self._containers)
