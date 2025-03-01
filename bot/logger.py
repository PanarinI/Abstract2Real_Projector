import logging
import os
from config import LOG_LEVEL, LOG_FORMAT, LOG_FILE

def setup_logging():
    """Настраивает логирование в зависимости от среды (локально или облако)."""
    IS_LOCAL = os.getenv("LOCAL_RUN", "false").lower() == "true"
 #  LOG_DIR = "logs"

    # Создаем папку logs, если её нет
 #   if IS_LOCAL and not os.path.exists(LOG_DIR):
 #       os.makedirs(LOG_DIR)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(LOG_LEVEL)

    # 🖥️ Логирование в консоль
    console_handler = logging.StreamHandler()
    console_handler.setLevel(LOG_LEVEL)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    root_logger.addHandler(console_handler)

    # 📄 Логирование в файл
    if IS_LOCAL and LOG_FILE:
    #   file_path = os.path.join(LOG_DIR, LOG_FILE) - ниже вместо LOG_FILE - 'file_path'
        file_handler = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
        file_handler.setLevel(LOG_LEVEL)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        root_logger.addHandler(file_handler)

    logging.info("✅ Логирование настроено! (Локально: %s, Файл: %s)", IS_LOCAL, LOG_FILE if IS_LOCAL else "Нет")

