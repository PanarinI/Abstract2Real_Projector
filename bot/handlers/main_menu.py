import json
import base64
import urllib.parse
from datetime import datetime

from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command  # Новый импорт

from bot.handlers.states import BrandCreationStates
from bot.services.brand_ask_ai import ask_ai
from bot.services.name_gen import gen_process_and_check
from bot.handlers.keyboards.name_generate import generate_username_kb


import logging

main_menu_router = Router()


# Функция для отображения главного меню
async def show_main_menu(message: types.Message):
    """
    Отображает главное меню с кнопками выбора действия.
    """
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🆕 Начать процесс", callback_data="create_brand")],
        [InlineKeyboardButton(text="🎲 Что это и зачем", callback_data="help")],
        [InlineKeyboardButton(text="🐾 Мастерская Бот и Кот", url="https://t.me/bot_and_kot")]
    ])

    await message.answer(
        "Вы в главном меню. Выберите действие:",
        reply_markup=kb
    )

# Универсальная клавиатура для возврата в меню
def back_to_menu_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏠 В меню", callback_data="start")]
        ]
    )


# Обработка нажатия кнопки «Вернуться в меню»
@main_menu_router.callback_query(lambda c: c.data == "start")
async def cmd_start_from_callback(query: types.CallbackQuery, state: FSMContext):
    await query.answer()  # Подтверждаем callback
    await state.clear()  # Очищаем состояние FSM
    await show_main_menu(query.message)


# 📍 Обработка команды /start
import urllib.parse

from bot.handlers.brand_gen import stage1_problem  # Убедись, что импорт есть

@main_menu_router.message(Command(commands=["start"]))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()  # Очищаем состояние FSM

    parts = message.text.split(maxsplit=1)
    if len(parts) > 1:
        args = parts[1].strip()
        # Декодируем URL-энкодинг, если он есть
        args = urllib.parse.unquote(args)
        try:
            print(f"ARGS: {args}")
            # Декодируем Base64 и затем JSON
            decoded_json = base64.urlsafe_b64decode(args.encode()).decode()
            data = json.loads(decoded_json)
            username = data.get("username")
            context = data.get("context")
        except Exception as e:
            logging.exception("Ошибка при разборе аргументов")
            # Если декодирование не удалось, используем аргумент как username, а context оставляем пустым
            username, context = args, None

        await state.update_data(username=username, context=context)
        await message.answer(f"🔹 Вы выбрали имя @{username}.")
        if context:
            await message.answer(f"💡 Ваша идея: {context}")

        # Устанавливаем состояние и запускаем Этап 1
        await state.set_state(BrandCreationStates.waiting_for_stage1)
        await stage1_problem(message, state)
    else:
        await show_main_menu(message)






# 📍 Обработчик кнопки «Начать процесс»
@main_menu_router.callback_query(lambda c: c.data == "create_brand")
async def start_brand_process(query: types.CallbackQuery, state: FSMContext):
    await query.answer()

    # Отправляем вступительное сообщение с кнопками
    await query.message.answer(
        "💡 У вас есть идея? Давайте сделаем из неё уникальный проект!\n"
        "✍️ Напишите свою идею ниже 👇",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎲 Получить случайную идею", callback_data="get_random_idea")],
            [InlineKeyboardButton(text="🏠 В меню", callback_data="start")]
        ])
    )

    # Переходим в состояние ожидания контекста
    await state.set_state(BrandCreationStates.waiting_for_context)



# Генерация случайной идеи (обработчик)
@main_menu_router.callback_query(lambda c: c.data == "get_random_idea")
async def generate_random_idea(query: types.CallbackQuery, state: FSMContext):
    await query.message.answer("⏳ Придумываю и выбираю свободные username...")
    await query.answer()

    # Генерация случайной идеи (3-6 слов)
    prompt = "Придумай уникальную и креативную идею для проекта. Идея должна состоять из 3-6 слов и быть максимально непохожей на предыдущие идеи. "
    random_idea = ask_ai(prompt).strip()

    if not random_idea:
        await query.message.answer("❌ Не удалось сгенерировать идею. Попробуйте ещё раз.")
        return

    logging.info(f"🎲 Случайная идея: {random_idea}")

    # Сохраняем случайную идею в FSM
    await state.update_data(context=random_idea, is_random=True)

    # Устанавливаем start_time для расчета duration
    start_time = datetime.now().isoformat()
    await state.update_data(start_time=start_time)

    # Запускаем генерацию username через perform_username_generation
    from bot.handlers.name_gen import perform_username_generation
    await perform_username_generation(query, state, query.bot, style=None)


# 📍 Обработчик кнопки «Что это и зачем?»
@main_menu_router.callback_query(lambda c: c.data == "help")
async def show_help(query: types.CallbackQuery):
    await query.answer()  # Подтверждаем callback

    # Создаем кнопку "В меню"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 В меню", callback_data="start")]
    ])

    await query.message.answer(
        "🧠 Этот генератор позволяет создать уникальный проект всего за 4 простых шага!\n\n"
        "💡 Уникальность подхода:\n"
        "1. Генератор проверяет свободность username в Telegram.\n"
        "2. Концепция проекта разрабатывается на основе ваших мыслей.\n"
        "3. Вы получаете готовый концепт, основанный на ваших уникальных выборах и уникальном username!\n\n"
        "🌟 Нажмите «Начать процесс», чтобы создать что-то уникальное прямо сейчас!\n",
        reply_markup=kb
    )
