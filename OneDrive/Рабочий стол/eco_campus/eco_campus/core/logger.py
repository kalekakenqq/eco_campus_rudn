"""
Настройка профессионального логирования для EcoCampus.

Логгер пишет одновременно в консоль и в файл logs/eco_campus.log.
Использование print() в коде приложения не допускается.
"""

import logging
import sys
from pathlib import Path

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Создаёт и возвращает настроенный логгер.

    Args:
        name: Имя логгера, обычно передаётся __name__ модуля.
        level: Уровень логирования по умолчанию.

    Returns:
        Готовый экземпляр Logger с обработчиками консоли и файла.
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(level)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
    logger.addHandler(console_handler)

    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    file_handler = logging.FileHandler(log_dir / "eco_campus.log", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
    logger.addHandler(file_handler)

    return logger


app_logger = setup_logger("eco_campus")
