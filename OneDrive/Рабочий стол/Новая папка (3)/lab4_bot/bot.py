import logging
import os
import sqlite3
from datetime import datetime

from dotenv import load_dotenv
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# Загружаем переменные из .env файла
load_dotenv()

# Настройка логирования — чтобы видеть что происходит в консоли
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler (многошаговый диалог)
NAME, AGE = range(2)


# ────────────────────────────────────────────────
# БАЗА ДАННЫХ
# ────────────────────────────────────────────────

def init_db():
    """Создаём таблицы при первом запуске."""
    conn = sqlite3.connect("bot.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id   INTEGER PRIMARY KEY,
            username  TEXT,
            name      TEXT,
            age       INTEGER,
            joined_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER,
            text       TEXT,
            sent_at    TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_user(user_id: int, username: str, name: str, age: int):
    """Сохраняем или обновляем пользователя в БД."""
    conn = sqlite3.connect("bot.db")
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO users (user_id, username, name, age, joined_at)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, username, name, age, datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    conn.close()


def save_message(user_id: int, text: str):
    """Логируем каждое сообщение пользователя в БД."""
    conn = sqlite3.connect("bot.db")
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO messages (user_id, text, sent_at)
        VALUES (?, ?, ?)
    """, (user_id, text, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()


def get_user(user_id: int):
    """Получаем пользователя из БД. Возвращает None если не найден."""
    conn = sqlite3.connect("bot.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row


def get_stats():
    """Возвращает общую статистику: кол-во пользователей и сообщений."""
    conn = sqlite3.connect("bot.db")
    cur = conn.cursor()
    users_count = cur.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    msg_count = cur.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
    conn.close()
    return users_count, msg_count


# ────────────────────────────────────────────────
# ОБРАБОТЧИКИ КОМАНД
# ────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start — приветствие с inline-кнопками."""
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("📝 Зарегистрироваться", callback_data="register")],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="help"),
         InlineKeyboardButton("📊 Статистика", callback_data="stats")],
    ]
    markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Привет, {user.first_name}! 👋\n\n"
        "Я учебный бот. Вот что я умею:\n"
        "• Регистрация через диалог\n"
        "• Повтор твоих сообщений\n"
        "• Показ статистики\n\n"
        "Выбери действие:",
        reply_markup=markup,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help — список команд."""
    text = (
        "📖 Доступные команды:\n\n"
        "/start — главное меню\n"
        "/help — эта справка\n"
        "/register — пройти регистрацию\n"
        "/profile — посмотреть свой профиль\n"
        "/stats — статистика бота\n"
        "/cancel — отменить текущий диалог\n\n"
        "Или просто напиши что-нибудь — я отвечу!"
    )
    await update.message.reply_text(text)


async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /profile — профиль пользователя из БД."""
    user_id = update.effective_user.id
    row = get_user(user_id)
    if row:
        # row = (user_id, username, name, age, joined_at)
        await update.message.reply_text(
            f"👤 Твой профиль:\n\n"
            f"Имя: {row[2]}\n"
            f"Возраст: {row[3]}\n"
            f"Дата регистрации: {row[4]}"
        )
    else:
        await update.message.reply_text(
            "Ты ещё не зарегистрирован.\n"
            "Нажми /register чтобы пройти регистрацию."
        )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /stats — общая статистика бота."""
    users, messages = get_stats()
    await update.message.reply_text(
        f"📊 Статистика бота:\n\n"
        f"👥 Пользователей: {users}\n"
        f"💬 Сообщений обработано: {messages}"
    )


# ────────────────────────────────────────────────
# РЕГИСТРАЦИЯ (ConversationHandler — многошаговый диалог)
# ────────────────────────────────────────────────

async def register_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Шаг 1 регистрации — спрашиваем имя."""
    # Может вызываться как командой /register, так и кнопкой
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(
            "📝 Начинаем регистрацию!\n\nКак тебя зовут?"
        )
    else:
        await update.message.reply_text(
            "📝 Начинаем регистрацию!\n\nКак тебя зовут?"
        )
    return NAME


async def got_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Шаг 2 — сохраняем имя, спрашиваем возраст."""
    name = update.message.text.strip()

    # Простая валидация
    if len(name) < 2 or len(name) > 50:
        await update.message.reply_text("Имя должно быть от 2 до 50 символов. Попробуй ещё раз:")
        return NAME

    context.user_data["name"] = name
    await update.message.reply_text(f"Отлично, {name}! Сколько тебе лет?")
    return AGE


async def got_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Шаг 3 — сохраняем возраст, завершаем регистрацию."""
    try:
        age = int(update.message.text.strip())
        if age < 5 or age > 120:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Введи корректный возраст (число от 5 до 120):")
        return AGE

    user = update.effective_user
    name = context.user_data["name"]

    # Сохраняем в базу данных
    save_user(user.id, user.username or "", name, age)

    await update.message.reply_text(
        f"✅ Регистрация завершена!\n\n"
        f"Имя: {name}\n"
        f"Возраст: {age}\n\n"
        f"Используй /profile чтобы посмотреть профиль."
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена диалога командой /cancel."""
    context.user_data.clear()
    await update.message.reply_text("❌ Действие отменено. Напиши /start чтобы начать заново.")
    return ConversationHandler.END


# ────────────────────────────────────────────────
# ОБРАБОТЧИК INLINE-КНОПОК
# ────────────────────────────────────────────────

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает нажатия на inline-кнопки."""
    query = update.callback_query
    await query.answer()  # Убираем анимацию загрузки на кнопке

    if query.data == "help":
        text = (
            "📖 Доступные команды:\n\n"
            "/start — главное меню\n"
            "/help — справка\n"
            "/register — регистрация\n"
            "/profile — мой профиль\n"
            "/stats — статистика"
        )
        await query.message.reply_text(text)

    elif query.data == "stats":
        users, messages = get_stats()
        await query.message.reply_text(
            f"📊 Статистика:\n\n"
            f"👥 Пользователей: {users}\n"
            f"💬 Сообщений: {messages}"
        )

    # "register" обрабатывается через ConversationHandler


# ────────────────────────────────────────────────
# ОБРАБОТЧИК ТЕКСТОВЫХ СООБЩЕНИЙ (эхо)
# ────────────────────────────────────────────────

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Повторяет сообщение пользователя и сохраняет его в БД."""
    text = update.message.text
    user_id = update.effective_user.id

    # Сохраняем сообщение в базу данных
    save_message(user_id, text)

    await update.message.reply_text(f"Ты написал: «{text}»")


# ────────────────────────────────────────────────
# ОБРАБОТЧИК ОШИБОК
# ────────────────────────────────────────────────

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Глобальный обработчик ошибок."""
    logger.error(f"Ошибка: {context.error}")


# ────────────────────────────────────────────────
# ТОЧКА ВХОДА
# ────────────────────────────────────────────────

def main():
    # Инициализируем базу данных
    init_db()

    # Получаем токен из .env файла
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN не найден! Создай файл .env с токеном.")

    # Создаём приложение
    app = Application.builder().token(token).build()

    # ConversationHandler — многошаговый диалог регистрации
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("register", register_start),
            CallbackQueryHandler(register_start, pattern="^register$"),
        ],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_name)],
            AGE:  [MessageHandler(filters.TEXT & ~filters.COMMAND, got_age)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Регистрируем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("profile", profile_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    app.add_error_handler(error_handler)

    print("Бот запущен! Нажми Ctrl+C для остановки.")
    app.run_polling()


if __name__ == "__main__":
    main()
