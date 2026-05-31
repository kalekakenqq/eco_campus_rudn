"""
Unit-тесты для модулей EcoCampus.
Покрывают: модели, исключения, маршрутизатор.
"""

import pytest

from eco_campus.core.exceptions import (
    ContainerNotFoundError,
    InvalidWasteTypeError,
    LocationNotFoundError,
    NoRouteError,
)
from eco_campus.core.models import (
    Container,
    Coordinates,
    Route,
    RouteStep,
    UserLocation,
    WasteType,
)
from eco_campus.core.router import CampusRouter


# ---------------------------------------------------------------------------
# Фикстуры
# ---------------------------------------------------------------------------

@pytest.fixture
def router() -> CampusRouter:
    """Возвращает экземпляр маршрутизатора с реальными данными кампуса."""
    return CampusRouter()


@pytest.fixture
def sample_container() -> Container:
    return Container(
        container_id="test_01",
        name="Тестовый контейнер",
        location_name="fountain",
        coordinates=Coordinates(55.6522, 37.5318),
        accepted_types=[WasteType.PLASTIC, WasteType.PAPER],
        working_hours="09:00–21:00",
    )


# ---------------------------------------------------------------------------
# Тесты моделей
# ---------------------------------------------------------------------------

class TestCoordinates:
    def test_valid_coordinates(self) -> None:
        coords = Coordinates(55.6522, 37.5318)
        assert coords.lat == 55.6522
        assert coords.lon == 37.5318

    def test_invalid_lat(self) -> None:
        with pytest.raises(ValueError):
            Coordinates(lat=91.0, lon=37.5)

    def test_invalid_lon(self) -> None:
        with pytest.raises(ValueError):
            Coordinates(lat=55.0, lon=181.0)

    def test_edge_valid(self) -> None:
        # Граничные корректные значения
        Coordinates(lat=90.0, lon=180.0)
        Coordinates(lat=-90.0, lon=-180.0)


class TestWasteType:
    def test_all_types_have_labels(self) -> None:
        for wt in WasteType:
            assert wt.label(), f"WasteType.{wt.name} не имеет метки"

    def test_label_not_empty(self) -> None:
        assert WasteType.PLASTIC.label() != ""
        assert WasteType.ELECTRONICS.label() != ""


class TestContainer:
    def test_accepts_correct_type(self, sample_container: Container) -> None:
        assert sample_container.accepts(WasteType.PLASTIC) is True
        assert sample_container.accepts(WasteType.PAPER) is True

    def test_rejects_wrong_type(self, sample_container: Container) -> None:
        assert sample_container.accepts(WasteType.GLASS) is False
        assert sample_container.accepts(WasteType.ELECTRONICS) is False

    def test_default_active(self, sample_container: Container) -> None:
        assert sample_container.is_active is True


class TestRoute:
    def test_summary_contains_key_info(self) -> None:
        container = Container(
            container_id="c_s",
            name="Экопункт тест",
            location_name="fountain",
            coordinates=Coordinates(55.65, 37.53),
            accepted_types=[WasteType.PLASTIC],
            working_hours="09:00–21:00",
        )
        route = Route(
            target_container=container,
            waste_type=WasteType.PLASTIC,
            steps=[],
            total_distance_meters=350.0,
            estimated_minutes=4.375,
        )
        summary = route.summary()
        assert "Экопункт тест" in summary
        assert "350" in summary

    def test_summary_km_when_long(self) -> None:
        container = Container(
            container_id="c_km",
            name="Дальний контейнер",
            location_name="back_exit",
            coordinates=Coordinates(55.65, 37.53),
            accepted_types=[WasteType.GLASS],
            working_hours="Круглосуточно",
        )
        route = Route(
            target_container=container,
            waste_type=WasteType.GLASS,
            total_distance_meters=1200.0,
            estimated_minutes=15.0,
        )
        assert "км" in route.summary()


# ---------------------------------------------------------------------------
# Тесты исключений
# ---------------------------------------------------------------------------

class TestExceptions:
    def test_location_not_found_message(self) -> None:
        exc = LocationNotFoundError("unknown_node")
        assert "unknown_node" in exc.message
        assert exc.code == "LOCATION_NOT_FOUND"

    def test_container_not_found_message(self) -> None:
        exc = ContainerNotFoundError("Стекло")
        assert "Стекло" in exc.message
        assert exc.code == "CONTAINER_NOT_FOUND"

    def test_no_route_message(self) -> None:
        exc = NoRouteError("point_a", "point_b")
        assert "point_a" in exc.message
        assert "point_b" in exc.message

    def test_invalid_waste_type(self) -> None:
        exc = InvalidWasteTypeError("garbage_xyz")
        assert "garbage_xyz" in exc.message


# ---------------------------------------------------------------------------
# Тесты маршрутизатора
# ---------------------------------------------------------------------------

class TestCampusRouter:
    def test_locations_not_empty(self, router: CampusRouter) -> None:
        locations = router.get_locations()
        assert len(locations) > 0

    def test_locations_have_display_names(self, router: CampusRouter) -> None:
        for loc in router.get_locations():
            assert loc.display_name, f"Нет display_name для {loc.node_id}"

    def test_find_plastic_containers(self, router: CampusRouter) -> None:
        containers = router.find_containers(WasteType.PLASTIC)
        assert len(containers) > 0
        for c in containers:
            assert c.accepts(WasteType.PLASTIC)

    def test_route_from_main_entrance_plastic(self, router: CampusRouter) -> None:
        route = router.find_nearest_route("main_entrance", WasteType.PLASTIC)
        assert route.total_distance_meters >= 0  # 0 означает контейнер на той же точке
        assert route.target_container.accepts(WasteType.PLASTIC)

    def test_route_estimated_time_positive(self, router: CampusRouter) -> None:
        route = router.find_nearest_route("dorm_2", WasteType.ELECTRONICS)
        assert route.estimated_minutes > 0

    def test_unknown_location_raises(self, router: CampusRouter) -> None:
        with pytest.raises(LocationNotFoundError) as exc_info:
            router.find_nearest_route("nowhere_land", WasteType.PLASTIC)
        assert "nowhere_land" in exc_info.value.message

    def test_route_steps_connected(self, router: CampusRouter) -> None:
        """Проверяет, что шаги маршрута образуют связный путь."""
        route = router.find_nearest_route("library", WasteType.PAPER)
        steps = route.steps
        for i in range(len(steps) - 1):
            assert steps[i].to_node == steps[i + 1].from_node, \
                "Шаги маршрута не связаны последовательно"

    def test_all_containers_returns_list(self, router: CampusRouter) -> None:
        containers = router.all_containers()
        assert isinstance(containers, list)
        assert len(containers) > 0

    def test_nearest_is_actually_nearest(self, router: CampusRouter) -> None:
        """Ближайший маршрут должен быть не длиннее любого другого."""
        wt = WasteType.PLASTIC
        route = router.find_nearest_route("fountain", wt)
        all_plastic = router.find_containers(wt)
        route_distance = route.total_distance_meters
        # Все пути к контейнерам должны быть >= найденного
        import networkx as nx
        for c in all_plastic:
            try:
                d = nx.dijkstra_path_length(
                    router._graph, "fountain", c.location_name, weight="weight"
                )
                assert d >= route_distance - 0.01  # допуск на float
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                pass
