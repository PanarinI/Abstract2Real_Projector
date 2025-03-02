import asyncpg
import os
import logging
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# 🔍 Определяем, локальный запуск или облачный
IS_LOCAL = os.getenv("LOCAL_RUN", "false").lower() == "true"

# ⚙️ Разные настройки БД для локального и облачного режима
DB_CONFIG = {
    "database": os.getenv("LOCAL_DB_NAME" if IS_LOCAL else "CLOUD_DB_NAME"),
    "user": os.getenv("LOCAL_DB_USER" if IS_LOCAL else "CLOUD_DB_USER"),
    "password": os.getenv("LOCAL_DB_PASSWORD" if IS_LOCAL else "CLOUD_DB_PASSWORD"),
    "host": os.getenv("LOCAL_DB_HOST" if IS_LOCAL else "CLOUD_DB_HOST"),
    "port": os.getenv("LOCAL_DB_PORT" if IS_LOCAL else "CLOUD_DB_PORT", "5432"),
}

logging.info(f"🔍 Используется база данных: {'ЛОКАЛЬНАЯ' if IS_LOCAL else 'ОБЛАЧНАЯ'}")
logging.info(f"    HOST = {DB_CONFIG['host']}")
logging.info(f"    DB NAME = {DB_CONFIG['database']}")
logging.info(f"    USER = {DB_CONFIG['user']}")
logging.info(f"    PASSWORD = {'✅' if DB_CONFIG['password'] else '❌ НЕ НАЙДЕНА'}")

# Глобальный пул соединений
pool = None


async def init_db_pool():
    """Создаёт пул соединений к БД при запуске приложения."""
    global pool
    try:
        logging.info(f"📡 Подключение к {'локальной' if IS_LOCAL else 'облачной'} БД: {DB_CONFIG['host']}")

        pool = await asyncpg.create_pool(
            database=DB_CONFIG["database"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            min_size=1,  # 📌 Минимум 1 соединение
            max_size=10  # 📌 Максимум 10 соединений
        )
        logging.info("✅ Пул соединений к БД создан.")
    except Exception as e:
        logging.error(f"❌ Ошибка при создании пула соединений: {e}")
        pool = None


async def get_connection():
    """Получает соединение из пула. Если пула нет — создаёт."""
    global pool
    if pool is None:
        logging.warning("⚠️ Пул соединений отсутствует, создаю...")
        await init_db_pool()  # Попытка создать пул

    if pool is None:
        logging.error("❌ Невозможно получить соединение — пул не создан.")
        return None

    return await pool.acquire()


async def close_db_pool():
    """Закрывает пул соединений при завершении работы."""
    global pool
    if pool:
        await pool.close()
        logging.info("✅ Пул соединений закрыт.")


async def init_db():
    """Создаёт таблицу, если её нет."""
    await init_db_pool()  # Гарантируем, что пул создан
    conn = await get_connection()
    if conn is None:
        logging.error("❌ Невозможно выполнить init_db — соединение не получено.")
        return
    try:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        CREATE_TABLE_SQL_PATH = os.path.join(BASE_DIR, "create_table.sql")

        if os.path.exists(CREATE_TABLE_SQL_PATH):
            with open(CREATE_TABLE_SQL_PATH, "r", encoding="utf-8") as file:
                create_table = file.read()

            await conn.execute(create_table)
            logging.info("✅ Таблица 'generated_usernames' проверена/создана.")
        else:
            logging.error(f"❌ Файл {CREATE_TABLE_SQL_PATH} не найден! Таблица не будет создана.")
    except Exception as e:
        logging.error(f"❌ Ошибка при создании таблицы: {e}")
    finally:
        await pool.release(conn)


async def save_username_to_db(username: str, status: str, context: str, category: str, style: str = "None",
                              llm: str = "None"):
    """Сохраняет username в базу данных."""
    conn = await get_connection()
    if conn is None:
        logging.error("❌ Невозможно выполнить save_username_to_db — соединение не получено.")
        return

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    INSERT_SQL_PATH = os.path.join(BASE_DIR, "insert_username.sql")

    if not os.path.exists(INSERT_SQL_PATH):
        logging.error("❌ INSERT_SQL не загружен! Файл insert_username.sql отсутствует.")
        return

    with open(INSERT_SQL_PATH, "r", encoding="utf-8") as file:
        INSERT_SQL = file.read()

    try:
        await conn.execute(INSERT_SQL, username, status, category, context, style, llm)
        logging.info(f"✅ Добавлен в БД: @{username} | {status} | {category} | {context} | {style} | {llm}")
    except Exception as e:
        logging.error(f"❌ Ошибка при сохранении в БД: {e}")
    finally:
        await pool.release(conn)
