"""
REST API для сервиса эко-логистики кампуса РУДН.
"""

import threading
import time
import webbrowser
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from eco_campus.core.exceptions import (
    ContainerNotFoundError,
    EcoCampusError,
    InvalidWasteTypeError,
    LocationNotFoundError,
    NoRouteError,
)
from eco_campus.core.logger import setup_logger
from eco_campus.core.models import WasteType
from eco_campus.core.router import CampusRouter

logger = setup_logger(__name__)

_router: CampusRouter | None = None
STATIC_DIR = Path(__file__).parent / "static"


def _open_browser() -> None:
    time.sleep(1.5)
    webbrowser.open("http://127.0.0.1:8000")


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[type-arg]
    global _router
    logger.info("Запуск EcoCampus API...")
    _router = CampusRouter()
    logger.info("API готов к работе")
    threading.Thread(target=_open_browser, daemon=True).start()
    yield
    logger.info("Завершение работы API")


app = FastAPI(
    title="EcoCampus РУДН",
    description="Интеллектуальная навигация по экопунктам кампуса РУДН",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class ContainerOut(BaseModel):
    container_id: str
    name: str
    location_name: str
    accepted_types: list[str]
    working_hours: str
    description: str
    lat: float
    lon: float


class RouteStepOut(BaseModel):
    from_node: str
    to_node: str
    distance_meters: float
    instruction: str


class RouteOut(BaseModel):
    container: ContainerOut
    waste_type: str
    steps: list[RouteStepOut]
    total_distance_meters: float
    estimated_minutes: float
    summary: str


class LocationOut(BaseModel):
    node_id: str
    display_name: str
    lat: float | None
    lon: float | None


def _get_router() -> CampusRouter:
    if _router is None:
        raise HTTPException(status_code=503, detail="Сервис маршрутизации не готов")
    return _router


def _container_to_out(c: Any) -> ContainerOut:
    return ContainerOut(
        container_id=c.container_id,
        name=c.name,
        location_name=c.location_name,
        accepted_types=[wt.label() for wt in c.accepted_types],
        working_hours=c.working_hours,
        description=c.description,
        lat=c.coordinates.lat,
        lon=c.coordinates.lon,
    )


@app.get("/", include_in_schema=False)
def root() -> FileResponse:
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/api", tags=["info"])
def api_info() -> dict[str, str]:
    return {
        "service": "EcoCampus РУДН",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/locations", response_model=list[LocationOut], tags=["navigation"])
def get_locations() -> list[LocationOut]:
    """Все доступные точки кампуса."""
    campus_router = _get_router()
    return [
        LocationOut(
            node_id=loc.node_id,
            display_name=loc.display_name,
            lat=loc.coordinates.lat if loc.coordinates else None,
            lon=loc.coordinates.lon if loc.coordinates else None,
        )
        for loc in campus_router.get_locations()
    ]


@app.get("/waste-types", tags=["info"])
def get_waste_types() -> list[dict[str, str]]:
    """Все поддерживаемые типы отходов."""
    return [{"value": wt.value, "label": wt.label()} for wt in WasteType]


@app.get("/containers", response_model=list[ContainerOut], tags=["containers"])
def get_containers(
    waste_type: str | None = Query(default=None, description="Фильтр по типу отходов"),
) -> list[ContainerOut]:
    """Все контейнеры с опциональной фильтрацией по типу отходов."""
    campus_router = _get_router()
    try:
        if waste_type:
            try:
                wt = WasteType(waste_type)
            except ValueError:
                raise InvalidWasteTypeError(waste_type)
            containers = campus_router.find_containers(wt)
        else:
            containers = campus_router.all_containers()
    except ContainerNotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message) from exc
    except InvalidWasteTypeError as exc:
        raise HTTPException(status_code=422, detail=exc.message) from exc
    return [_container_to_out(c) for c in containers]


@app.get("/route", response_model=RouteOut, tags=["navigation"])
def get_route(
    from_location: str = Query(..., description="ID стартовой точки"),
    waste_type: str = Query(..., description="Тип отходов"),
) -> RouteOut:
    """Строит маршрут от указанной точки до ближайшего подходящего контейнера."""
    campus_router = _get_router()
    try:
        wt = WasteType(waste_type)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Неизвестный тип отходов: {waste_type!r}")
    try:
        route = campus_router.find_nearest_route(from_location, wt)
    except LocationNotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message) from exc
    except ContainerNotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message) from exc
    except NoRouteError as exc:
        raise HTTPException(status_code=404, detail=exc.message) from exc
    except EcoCampusError as exc:
        logger.exception("Неожиданная ошибка маршрутизации")
        raise HTTPException(status_code=500, detail=exc.message) from exc

    return RouteOut(
        container=_container_to_out(route.target_container),
        waste_type=route.waste_type.label(),
        steps=[
            RouteStepOut(
                from_node=s.from_node,
                to_node=s.to_node,
                distance_meters=s.distance_meters,
                instruction=s.instruction,
            )
            for s in route.steps
        ],
        total_distance_meters=route.total_distance_meters,
        estimated_minutes=route.estimated_minutes,
        summary=route.summary(),
    )
