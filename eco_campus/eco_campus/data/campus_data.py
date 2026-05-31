"""
База данных узлов графа и контейнеров кампуса РУДН.

Координаты зданий основаны на реальном расположении объектов
на улице Миклухо-Маклая, Москва (55.6519, 37.4825).
"""

from eco_campus.core.models import Container, Coordinates, WasteType

CAMPUS_NODES: dict[str, dict] = {
    "main_entrance": {
        "display": "Главный вход РУДН (Миклухо-Маклая, 6)",
        "coords": Coordinates(55.6492, 37.4843),
    },
    "main_building": {
        "display": "Главный корпус РУДН (Миклухо-Маклая, 6)",
        "coords": Coordinates(55.6501, 37.4838),
    },
    "building_8": {
        "display": "Корпус АТИ (Миклухо-Маклая, 8к2)",
        "coords": Coordinates(55.6518, 37.4821),
    },
    "building_10": {
        "display": "Корпус 10/2",
        "coords": Coordinates(55.6534, 37.4809),
    },
    "building_5": {
        "display": "Корпус 5",
        "coords": Coordinates(55.6525, 37.4815),
    },
    "library": {
        "display": "Научная библиотека РУДН",
        "coords": Coordinates(55.6508, 37.4852),
    },
    "interclub": {
        "display": "Интерклуб РУДН",
        "coords": Coordinates(55.6545, 37.4798),
    },
    "canteen": {
        "display": "Студенческая столовая РУДН",
        "coords": Coordinates(55.6512, 37.4831),
    },
    "sports_complex": {
        "display": "Спортивный комплекс РУДН",
        "coords": Coordinates(55.6498, 37.4862),
    },
    "medical_center": {
        "display": "Медицинский центр РУДН",
        "coords": Coordinates(55.6503, 37.4857),
    },
    "dorm_complex": {
        "display": "Комплекс общежитий (Миклухо-Маклая, 3)",
        "coords": Coordinates(55.6558, 37.4787),
    },
    "dorm_north": {
        "display": "Общежития — северный блок",
        "coords": Coordinates(55.6571, 37.4778),
    },
    "park": {
        "display": "Парк кампуса РУДН",
        "coords": Coordinates(55.6562, 37.4772),
    },
    "fii_building": {
        "display": "Корпус ФИИ (Подольское ш., 8с5)",
        "coords": Coordinates(55.6891, 37.6102),
    },
}

CAMPUS_EDGES: list[tuple[str, str, float]] = [
    ("main_entrance", "main_building", 100),
    ("main_entrance", "sports_complex", 180),
    ("main_entrance", "library", 150),
    ("main_building", "canteen", 90),
    ("main_building", "building_8", 200),
    ("main_building", "library", 120),
    ("building_8", "canteen", 100),
    ("building_8", "building_10", 180),
    ("building_8", "building_5", 120),
    ("building_10", "interclub", 130),
    ("building_10", "dorm_complex", 280),
    ("building_5", "building_10", 100),
    ("interclub", "dorm_complex", 150),
    ("dorm_complex", "dorm_north", 130),
    ("dorm_complex", "park", 100),
    ("dorm_north", "park", 100),
    ("canteen", "library", 110),
    ("canteen", "medical_center", 60),
    ("library", "sports_complex", 100),
    ("sports_complex", "medical_center", 70),
    ("sports_complex", "main_entrance", 180),
]

CONTAINERS: list[Container] = [
    Container(
        container_id="c01",
        name="Экопункт у главного входа",
        location_name="main_entrance",
        coordinates=Coordinates(55.6492, 37.4843),
        accepted_types=[WasteType.PLASTIC, WasteType.PAPER, WasteType.METAL],
        working_hours="08:00-22:00",
        description="Раздельные контейнеры у КПП главного входа",
    ),
    Container(
        container_id="c02",
        name="Экопункт у библиотеки",
        location_name="library",
        coordinates=Coordinates(55.6508, 37.4852),
        accepted_types=[WasteType.PAPER, WasteType.ELECTRONICS],
        working_hours="09:00-20:00",
        description="Приём макулатуры и старых учебников",
    ),
    Container(
        container_id="c03",
        name="Экопункт у столовой",
        location_name="canteen",
        coordinates=Coordinates(55.6512, 37.4831),
        accepted_types=[WasteType.PLASTIC, WasteType.GLASS, WasteType.ORGANIC, WasteType.METAL],
        working_hours="07:00-23:00",
        description="Основная точка рядом со студенческой столовой",
    ),
    Container(
        container_id="c04",
        name="Экопункт у общежитий",
        location_name="dorm_complex",
        coordinates=Coordinates(55.6558, 37.4787),
        accepted_types=[WasteType.PLASTIC, WasteType.PAPER, WasteType.GLASS, WasteType.METAL],
        working_hours="Круглосуточно",
        description="Доступен круглосуточно для жителей общежитий",
    ),
    Container(
        container_id="c05",
        name="Экопункт в парке кампуса",
        location_name="park",
        coordinates=Coordinates(55.6562, 37.4772),
        accepted_types=[WasteType.MIXED, WasteType.ORGANIC],
        working_hours="08:00-21:00",
        description="Контейнеры в зелёной зоне кампуса",
    ),
    Container(
        container_id="c06",
        name="Экопункт у спорткомплекса",
        location_name="sports_complex",
        coordinates=Coordinates(55.6498, 37.4862),
        accepted_types=[WasteType.PLASTIC, WasteType.TEXTILE, WasteType.METAL],
        working_hours="07:00-22:00",
        description="Приём спортивной одежды и инвентаря",
    ),
    Container(
        container_id="c07",
        name="Экопункт у корпуса ФИИ",
        location_name="fii_building",
        coordinates=Coordinates(55.6891, 37.6102),
        accepted_types=[WasteType.ELECTRONICS, WasteType.PAPER, WasteType.PLASTIC],
        working_hours="09:00-19:00",
        description="Сбор электронного мусора и батареек (Подольское ш., 8с5)",
    ),
]
