import logging
import asyncio
import os
import json
import sys
import time


sys.path.insert(0, "/app")
sys.path.insert(0, "/app/bot")

print(f"🔍 sys.path: {sys.path}")  # Логируем пути
print(f"🔍 Текущая директория: {os.getcwd()}")  # Логируем рабочую директорию
print(f"📂 Файлы в /app: {os.listdir('/app')}")
if os.path.exists("/app/bot"):
    print(f"📂 Файлы в /app/bot: {os.listdir('/app/bot')}")
else:
    print("❌ Папка /app/bot НЕ НАЙДЕНА!")

from aiohttp import web
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update
# 📌 Устанавливаем корректный путь (для Amverag)
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from bot.handlers.name_gen import username_router
from bot.handlers.brand_gen import brand_router
from bot.handlers.main_menu import main_menu_router
from database.database import init_db, init_db_pool
from logger import setup_logging

setup_logging()
load_dotenv()


sys.path.append("/app")  # 🔥 Принудительно добавляем /app
sys.path.append("/app/bot")  # 🔥 Добавляем /app/bot, если не поможет

print(f"🔍 sys.path: {sys.path}")  # Логируем пути
print(f"🔍 Текущая директория: {os.getcwd()}")  # Логируем рабочую директорию
logging.info(f"🔍 sys.path: {sys.path}")
logging.info(f"🔍 Текущая директория: {os.getcwd()}")

print(f"📂 Файлы в /app: {os.listdir('/app')}")
if os.path.exists("/app/bot"):
    print(f"📂 Файлы в /app/bot: {os.listdir('/app/bot')}")
else:
    print("❌ Папка /app/bot НЕ НАЙДЕНА!")

# === 🔍 Определяем режим работы ===
IS_LOCAL = os.getenv("LOCAL_RUN", "false").lower() == "true"

# === 🌍 Настройки Webhook ===
WEBHOOK_HOST = os.getenv("WEBHOOK_URL", "https://prozektor-panarini.amvera.io").strip()
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}".replace("http://", "https://")

# === 🌐 Настройки Web-сервера ===
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("WEBHOOK_PORT", 80))  # Можно задать через .env

# Инициализация бота
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in .env file")

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
dp.bot = bot  # Привязываем бота к диспетчеру вручную

# Подключаем роутеры
dp.include_router(main_menu_router)
dp.include_router(username_router)
dp.include_router(brand_router)


async def on_startup():
    """Запуск бота и подключение к БД"""
    await init_db_pool()  # 📌 Добавить вызов, если его нет
    await init_db()  # ✅ Проверка таблиц


    if IS_LOCAL:
        logging.info("🛑 Локальный запуск. Webhook НЕ будет установлен.")
        await bot.delete_webhook(drop_pending_updates=True)
    else:
        logging.info(f"🔗 Устанавливаем вебхук: {WEBHOOK_URL}")
        try:
            await bot.delete_webhook(drop_pending_updates=True)
            await bot.set_webhook(WEBHOOK_URL)
            logging.info(f"✅ Webhook установлен: {WEBHOOK_URL}")
        except Exception as e:
            logging.error(f"❌ Ошибка при установке Webhook: {e}")
            sys.exit(1)


async def on_shutdown(_):
    """Закрытие сессии перед остановкой"""
    logging.info("🚨 Бот остановлен! Закрываю сессию...")
    try:
        await bot.session.close()
    except Exception as e:
        logging.error(f"❌ Ошибка при закрытии сессии: {e}")
    logging.info("✅ Сессия закрыта.")


async def handle_update(request):
    """Обработчик Webhook (принимает входящие запросы от Telegram)"""
    time_start = time.time()
    raw_text = await request.text()

    try:
        update_data = json.loads(raw_text)
        update = Update(**update_data)
        await dp.feed_update(bot=bot, update=update)

        time_end = time.time()
        logging.info(f"⏳ Обработка запроса заняла {time_end - time_start:.4f} секунд")
        return web.Response()

    except json.JSONDecodeError:
        logging.error(f"❌ Ошибка парсинга JSON: {raw_text}")

    except Exception as e:
        logging.error(f"❌ Ошибка обработки Webhook: {e}", exc_info=True)
        return web.Response(status=500)


async def handle_root(request):
    """Обработчик корневого запроса (проверка работы)"""
    logging.info("✅ Обработан GET-запрос на /")
    return web.Response(text="✅ Бот работает!", content_type="text/plain")


async def main():
    """Главная функция запуска"""
    await on_startup()

    if IS_LOCAL:
        logging.info("🚀 Запускаем бота в режиме Polling...")
        await dp.start_polling(bot)
        sys.exit(0)

    logging.info("⚡ БОТ ПЕРЕЗАПУЩЕН (контейнер стартовал заново)")
    app = web.Application()
    app.add_routes([
        web.get("/", handle_root),
        web.post("/webhook", handle_update)
    ])
    app.on_shutdown.append(on_shutdown)
    return app


async def start_server():
    """Запуск сервера или Polling"""
    try:
        app = await main()

        if IS_LOCAL:
            logging.info("🚀 Запускаем бота в режиме Polling...")
            await dp.start_polling(bot)
            sys.exit(0)

        # 🌍 Webhook Mode
        logging.info("✅ Запускаем бота в режиме Webhook...")
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", WEBAPP_PORT)
        await site.start()

        logging.info(f"✅ Webhook сервер запущен на порту {WEBAPP_PORT}")

        await asyncio.Event().wait()

    except Exception as e:
        logging.error(f"❌ Ошибка запуска: {e}")
        sys.exit(1)


logging.getLogger("asyncio").setLevel(logging.WARNING)


if __name__ == "__main__":
    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        logging.info("🛑 Бот остановлен пользователем.")
    except Exception as e:
        logging.error(f"❌ Критическая ошибка: {e}")

    while True:
        time.sleep(3600)  # Держим процесс живым
