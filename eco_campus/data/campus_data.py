"""
База данных контейнеров и узлов карты кампуса РУДН.
Данные основаны на реальной планировке кампуса РУДН (Москва).
"""

from eco_campus.core.models import Container, Coordinates, WasteType

# ---------------------------------------------------------------------------
# Узлы графа кампуса (ключевые точки для навигации)
# ---------------------------------------------------------------------------

CAMPUS_NODES: dict[str, dict] = {
    # Главный вход и центральная аллея
    "main_entrance": {
        "display": "Главный вход (ул. Миклухо-Маклая)",
        "coords": Coordinates(55.6496, 37.5303),
    },
    "central_alley": {
        "display": "Центральная аллея",
        "coords": Coordinates(55.6510, 37.5310),
    },
    "fountain": {
        "display": "Фонтан (центр кампуса)",
        "coords": Coordinates(55.6522, 37.5318),
    },
    # Учебные корпуса
    "building_a": {
        "display": "Корпус А (Инженерный)",
        "coords": Coordinates(55.6530, 37.5295),
    },
    "building_b": {
        "display": "Корпус Б (Гуманитарный)",
        "coords": Coordinates(55.6535, 37.5325),
    },
    "building_6": {
        "display": "Корпус 6 (ФИИ)",
        "coords": Coordinates(55.6518, 37.5340),
    },
    "library": {
        "display": "Научная библиотека",
        "coords": Coordinates(55.6515, 37.5280),
    },
    # Общежития
    "dorm_1": {
        "display": "Общежитие №1",
        "coords": Coordinates(55.6542, 37.5350),
    },
    "dorm_2": {
        "display": "Общежитие №2",
        "coords": Coordinates(55.6550, 37.5340),
    },
    "dorm_3": {
        "display": "Общежитие №3",
        "coords": Coordinates(55.6558, 37.5325),
    },
    # Инфраструктура
    "canteen": {
        "display": "Студенческая столовая",
        "coords": Coordinates(55.6525, 37.5360),
    },
    "sports_complex": {
        "display": "Спортивный комплекс",
        "coords": Coordinates(55.6505, 37.5350),
    },
    "medical_center": {
        "display": "Медицинский центр",
        "coords": Coordinates(55.6500, 37.5330),
    },
    "park_north": {
        "display": "Северный парк",
        "coords": Coordinates(55.6560, 37.5310),
    },
    "back_exit": {
        "display": "Северный выход",
        "coords": Coordinates(55.6568, 37.5318),
    },
}

# ---------------------------------------------------------------------------
# Рёбра графа (пешеходные пути между узлами), расстояния в метрах
# ---------------------------------------------------------------------------

CAMPUS_EDGES: list[tuple[str, str, float]] = [
    ("main_entrance", "central_alley", 120),
    ("central_alley", "fountain", 150),
    ("central_alley", "library", 90),
    ("central_alley", "medical_center", 110),
    ("fountain", "building_a", 130),
    ("fountain", "building_b", 100),
    ("fountain", "building_6", 140),
    ("fountain", "canteen", 160),
    ("building_b", "dorm_1", 200),
    ("building_6", "canteen", 80),
    ("canteen", "dorm_1", 120),
    ("canteen", "dorm_2", 150),
    ("dorm_1", "dorm_2", 60),
    ("dorm_2", "dorm_3", 60),
    ("dorm_3", "park_north", 100),
    ("park_north", "back_exit", 80),
    ("sports_complex", "central_alley", 130),
    ("sports_complex", "medical_center", 70),
    ("sports_complex", "canteen", 180),
    ("library", "building_a", 100),
    ("building_a", "building_6", 200),
]

# ---------------------------------------------------------------------------
# Контейнеры для сортировки отходов
# ---------------------------------------------------------------------------

CONTAINERS: list[Container] = [
    Container(
        container_id="c01",
        name="Экопункт у главного входа",
        location_name="main_entrance",
        coordinates=Coordinates(55.6497, 37.5305),
        accepted_types=[WasteType.PLASTIC, WasteType.PAPER, WasteType.METAL],
        working_hours="08:00–22:00",
        description="Раздельные контейнеры у КПП",
    ),
    Container(
        container_id="c02",
        name="Экопункт у библиотеки",
        location_name="library",
        coordinates=Coordinates(55.6516, 37.5281),
        accepted_types=[WasteType.PAPER, WasteType.ELECTRONICS],
        working_hours="09:00–20:00",
        description="Приём макулатуры и старых учебников",
    ),
    Container(
        container_id="c03",
        name="Экопункт у столовой",
        location_name="canteen",
        coordinates=Coordinates(55.6526, 37.5361),
        accepted_types=[WasteType.PLASTIC, WasteType.GLASS, WasteType.ORGANIC, WasteType.METAL],
        working_hours="07:00–23:00",
        description="Основная точка у студенческой столовой",
    ),
    Container(
        container_id="c04",
        name="Экопункт у общежития №2",
        location_name="dorm_2",
        coordinates=Coordinates(55.6551, 37.5341),
        accepted_types=[WasteType.PLASTIC, WasteType.PAPER, WasteType.GLASS, WasteType.METAL],
        working_hours="Круглосуточно",
        description="Доступен 24/7 для жителей общежитий",
    ),
    Container(
        container_id="c05",
        name="Экопункт в северном парке",
        location_name="park_north",
        coordinates=Coordinates(55.6561, 37.5311),
        accepted_types=[WasteType.MIXED, WasteType.ORGANIC],
        working_hours="08:00–21:00",
        description="Контейнеры в зоне отдыха",
    ),
    Container(
        container_id="c06",
        name="Экопункт у спорткомплекса",
        location_name="sports_complex",
        coordinates=Coordinates(55.6506, 37.5351),
        accepted_types=[WasteType.PLASTIC, WasteType.TEXTILE, WasteType.METAL],
        working_hours="07:00–22:00",
        description="Приём спортивной одежды и инвентаря",
    ),
    Container(
        container_id="c07",
        name="Экопункт у корпуса 6 (ФИИ)",
        location_name="building_6",
        coordinates=Coordinates(55.6519, 37.5341),
        accepted_types=[WasteType.ELECTRONICS, WasteType.PAPER, WasteType.PLASTIC],
        working_hours="09:00–19:00",
        description="Сбор электронного мусора и батареек",
    ),
]
