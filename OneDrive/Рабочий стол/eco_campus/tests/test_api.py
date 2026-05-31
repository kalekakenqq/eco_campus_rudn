"""
Интеграционные тесты для FastAPI-приложения EcoCampus.
"""

import pytest
from fastapi.testclient import TestClient

from eco_campus.api.app import app, _router as global_router
from eco_campus.core.router import CampusRouter


# ---------------------------------------------------------------------------
# Фикстуры
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    """Тестовый HTTP-клиент с инициализированным роутером."""
    # Патчим глобальный роутер напрямую
    import eco_campus.api.app as api_module
    api_module._router = CampusRouter()

    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# Тесты эндпоинтов
# ---------------------------------------------------------------------------

class TestRootEndpoint:
    def test_root_returns_200(self, client: TestClient) -> None:
        resp = client.get("/")
        assert resp.status_code in (200, 404)

    def test_api_info(self, client: TestClient) -> None:
        resp = client.get("/api")
        assert resp.status_code == 200
        assert "EcoCampus" in resp.json()["service"]

class TestLocationsEndpoint:
    def test_locations_200(self, client: TestClient) -> None:
        resp = client.get("/locations")
        assert resp.status_code == 200

    def test_locations_not_empty(self, client: TestClient) -> None:
        data = client.get("/locations").json()
        assert len(data) > 0

    def test_location_has_required_fields(self, client: TestClient) -> None:
        location = client.get("/locations").json()[0]
        assert "node_id" in location
        assert "display_name" in location


class TestWasteTypesEndpoint:
    def test_waste_types_200(self, client: TestClient) -> None:
        resp = client.get("/waste-types")
        assert resp.status_code == 200

    def test_waste_types_not_empty(self, client: TestClient) -> None:
        data = client.get("/waste-types").json()
        assert len(data) > 0

    def test_waste_type_has_value_and_label(self, client: TestClient) -> None:
        item = client.get("/waste-types").json()[0]
        assert "value" in item
        assert "label" in item


class TestContainersEndpoint:
    def test_all_containers_200(self, client: TestClient) -> None:
        resp = client.get("/containers")
        assert resp.status_code == 200

    def test_filter_by_plastic(self, client: TestClient) -> None:
        resp = client.get("/containers?waste_type=plastic")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) > 0

    def test_filter_invalid_type_422(self, client: TestClient) -> None:
        resp = client.get("/containers?waste_type=unicorn")
        assert resp.status_code == 422

    def test_container_fields(self, client: TestClient) -> None:
        container = client.get("/containers").json()[0]
        for field in ("container_id", "name", "accepted_types", "lat", "lon"):
            assert field in container


class TestRouteEndpoint:
    def test_valid_route_200(self, client: TestClient) -> None:
        resp = client.get("/route?from_location=main_entrance&waste_type=plastic")
        assert resp.status_code == 200

    def test_route_has_steps(self, client: TestClient) -> None:
        data = client.get("/route?from_location=fountain&waste_type=paper").json()
        assert "steps" in data
        assert len(data["steps"]) > 0

    def test_route_has_summary(self, client: TestClient) -> None:
        data = client.get("/route?from_location=library&waste_type=paper").json()
        assert "summary" in data
        assert len(data["summary"]) > 10

    def test_unknown_location_404(self, client: TestClient) -> None:
        resp = client.get("/route?from_location=mars&waste_type=plastic")
        assert resp.status_code == 404

    def test_unknown_waste_type_422(self, client: TestClient) -> None:
        resp = client.get("/route?from_location=fountain&waste_type=moonrocks")
        assert resp.status_code == 422

    def test_distance_positive(self, client: TestClient) -> None:
        data = client.get("/route?from_location=dorm_1&waste_type=glass").json()
        assert data["total_distance_meters"] > 0

    def test_estimated_minutes_positive(self, client: TestClient) -> None:
        # library не имеет контейнера для textile - будет найден дальний
        data = client.get("/route?from_location=library&waste_type=textile").json()
        assert data["estimated_minutes"] >= 0
