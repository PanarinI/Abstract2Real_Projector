import logging
import asyncio
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from bot.handlers.name_gen import username_router
from bot.handlers.brand_gen import brand_router
from bot.handlers.main_menu import main_menu_router  # Подключаем главный роутер
from database.database import init_db
from logger import setup_logging

setup_logging()
# Загрузка переменных окружения из .env
load_dotenv()

init_db() # запуск БД

# Инициализация бота и диспетчера
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in .env file")

# Инициализация бота без parse_mode
bot = Bot(token=BOT_TOKEN)

storage = MemoryStorage()
dp = Dispatcher(storage=storage)
dp.bot = bot  # Привязка бота к диспетчеру вручную

# Логирование
logging.basicConfig(level=logging.INFO)

# Подключение всех обработчиков (routers) после инициализации dp
dp.include_router(main_menu_router)
dp.include_router(username_router)
dp.include_router(brand_router)




# 📍 Обработчик команды /start
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "Здесь и сейчас вы разработаете уникальный проект из того, о чем вы сейчас думаете. Просто попробуйте - вас это может удивить\n"
        "Выбери действие:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🆕 Начать процесс", callback_data="create_brand")],
            [InlineKeyboardButton(text="🎲 Что это и зачем", callback_data="help")],  # Изменено callback_data
            [InlineKeyboardButton(text="🐾 Мастерская Бот и Кот", url="https://t.me/bot_and_kot")],
        ])
    )


async def on_startup():
    await init_db()  # ✅ Запускаем пул соединений к БД один раз

async def main():
    logging.info("🚀 Запуск бота...")
    await on_startup()  # Инициализируем БД перед стартом
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
