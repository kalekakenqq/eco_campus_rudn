"""
Telegram-бот для эко-навигации по кампусу РУДН.
Предоставляет интерфейс выбора локации и типа отходов,
и выдаёт маршрут до ближайшего контейнера.
"""

import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

from eco_campus.core.exceptions import (
    ContainerNotFoundError,
    EcoCampusError,
    LocationNotFoundError,
    NoRouteError,
)
from eco_campus.core.logger import setup_logger
from eco_campus.core.models import WasteType
from eco_campus.core.router import CampusRouter

logger = setup_logger(__name__)

ROUTER = CampusRouter()

# Ключи для хранения состояния в context.user_data
KEY_LOCATION = "selected_location"
KEY_WASTE = "selected_waste"


# ---------------------------------------------------------------------------
# Команды
# ---------------------------------------------------------------------------

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Приветственное сообщение и выбор локации."""
    await _ask_location(update, context)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "🌿 *EcoCampus РУДН* — навигатор к экопунктам\n\n"
        "Команды:\n"
        "/start — начать поиск маршрута\n"
        "/containers — показать все экопункты\n"
        "/help — справка\n\n"
        "Просто выберите своё местоположение и тип отходов — "
        "бот найдёт ближайший контейнер и построит маршрут!"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def cmd_containers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает все контейнеры с принимаемыми типами отходов."""
    containers = ROUTER.all_containers()
    lines = ["♻️ *Все экопункты кампуса РУДН:*\n"]
    for c in containers:
        types_str = ", ".join(wt.label() for wt in c.accepted_types)
        lines.append(f"📍 *{c.name}*\nПринимает: {types_str}\n🕐 {c.working_hours}\n")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


# ---------------------------------------------------------------------------
# Выбор локации
# ---------------------------------------------------------------------------

async def _ask_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    locations = ROUTER.get_locations()
    keyboard = [
        [InlineKeyboardButton(loc.display_name, callback_data=f"loc:{loc.node_id}")]
        for loc in locations
    ]
    markup = InlineKeyboardMarkup(keyboard)
    text = "📍 *Где вы сейчас находитесь?*\nВыберите ближайшую точку кампуса:"

    if update.message:
        await update.message.reply_text(text, reply_markup=markup, parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=markup, parse_mode="Markdown")


# ---------------------------------------------------------------------------
# Выбор типа отходов
# ---------------------------------------------------------------------------

async def _ask_waste_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    waste_icons = {
        WasteType.PLASTIC: "🧴",
        WasteType.PAPER: "📄",
        WasteType.GLASS: "🍶",
        WasteType.METAL: "🥫",
        WasteType.TEXTILE: "👕",
        WasteType.ELECTRONICS: "🔋",
        WasteType.ORGANIC: "🍃",
        WasteType.MIXED: "🗑",
    }
    keyboard = [
        [InlineKeyboardButton(
            f"{waste_icons.get(wt, '')} {wt.label()}",
            callback_data=f"waste:{wt.value}"
        )]
        for wt in WasteType
    ]
    keyboard.append([InlineKeyboardButton("⬅️ Изменить локацию", callback_data="back:location")])
    markup = InlineKeyboardMarkup(keyboard)

    location_name = context.user_data.get(KEY_LOCATION, "?")
    await update.callback_query.edit_message_text(
        f"✅ Локация: *{location_name}*\n\n♻️ *Что нужно выбросить?*",
        reply_markup=markup,
        parse_mode="Markdown",
    )


# ---------------------------------------------------------------------------
# Callback-обработчики
# ---------------------------------------------------------------------------

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    data: str = query.data or ""

    if data.startswith("loc:"):
        node_id = data.removeprefix("loc:")
        # Найдём красивое имя
        locations = {loc.node_id: loc.display_name for loc in ROUTER.get_locations()}
        context.user_data[KEY_LOCATION] = locations.get(node_id, node_id)
        context.user_data["location_id"] = node_id
        await _ask_waste_type(update, context)

    elif data.startswith("waste:"):
        waste_value = data.removeprefix("waste:")
        location_id: str = context.user_data.get("location_id", "")

        if not location_id:
            await query.edit_message_text("⚠️ Сначала выберите локацию. Нажмите /start")
            return

        try:
            wt = WasteType(waste_value)
            route = ROUTER.find_nearest_route(location_id, wt)
        except (LocationNotFoundError, ContainerNotFoundError, NoRouteError) as exc:
            logger.warning("Ошибка маршрутизации для пользователя: %s", exc)
            await query.edit_message_text(
                f"😔 {exc.message}\n\nПопробуйте выбрать другую локацию или тип отходов.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔄 Начать заново", callback_data="back:start")
                ]]),
            )
            return
        except EcoCampusError as exc:
            logger.exception("Неожиданная ошибка")
            await query.edit_message_text(f"❌ Внутренняя ошибка: {exc.message}")
            return

        steps_text = "\n".join(f"  {i+1}. {s.instruction}" for i, s in enumerate(route.steps))
        response = (
            f"🗺 *Маршрут найден!*\n\n"
            f"{route.summary()}\n\n"
            f"*Пошаговый маршрут:*\n{steps_text}"
        )

        keyboard = [[
            InlineKeyboardButton("🔄 Новый маршрут", callback_data="back:start"),
            InlineKeyboardButton("📋 Все экопункты", callback_data="show:all"),
        ]]
        await query.edit_message_text(
            response,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    elif data == "back:location":
        await _ask_location(update, context)

    elif data == "back:start":
        context.user_data.clear()
        await _ask_location(update, context)

    elif data == "show:all":
        containers = ROUTER.all_containers()
        lines = ["♻️ *Все экопункты:*\n"]
        for c in containers:
            types_str = ", ".join(wt.label() for wt in c.accepted_types)
            lines.append(f"📍 *{c.name}*\n{types_str}\n🕐 {c.working_hours}\n")
        await query.edit_message_text(
            "\n".join(lines),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Назад", callback_data="back:start")
            ]]),
            parse_mode="Markdown",
        )


# ---------------------------------------------------------------------------
# Запуск бота
# ---------------------------------------------------------------------------

def run_bot() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не задан в переменных окружения")
        raise EnvironmentError("TELEGRAM_BOT_TOKEN is required")

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("containers", cmd_containers))
    app.add_handler(CallbackQueryHandler(handle_callback))

    logger.info("Telegram-бот запущен")
    app.run_polling()


if __name__ == "__main__":
    run_bot()
