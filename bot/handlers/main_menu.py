from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command  # Новый импорт

from bot.handlers.states import BrandCreationStates

main_menu_router = Router()


# Функция для отображения главного меню
async def show_main_menu(message: types.Message):
    """
    Отображает главное меню с кнопками выбора действия.
    """
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🆕 Начать процесс", callback_data="create_brand")],
        [InlineKeyboardButton(text="🎲 Что это и зачем", callback_data="help")],
        [InlineKeyboardButton(text="🐾 Мастерская Бот и Кот", url="https://t.me/bot_and_cat")]
    ])

    await message.answer(
        "Вы в главном меню. Выберите действие:",
        reply_markup=kb
    )



# Обработка нажатия кнопки «Вернуться в меню»
@main_menu_router.callback_query(lambda c: c.data == "start")
async def cmd_start_from_callback(query: types.CallbackQuery, state: FSMContext):
    await query.answer()  # Подтверждаем callback
    await state.clear()  # Очищаем состояние FSM
    await show_main_menu(query.message)


# 📍 Обработка команды /start (правильный синтаксис для Aiogram 3.x)
@main_menu_router.message(Command(commands=["start"]))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()  # Очищаем состояние FSM
    await show_main_menu(message)


# 📍 Обработчик кнопки «Начать процесс»
@main_menu_router.callback_query(lambda c: c.data == "create_brand")
async def start_brand_process(query: types.CallbackQuery, state: FSMContext):
    await query.answer()  # Подтверждаем callback
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Вернуться в меню", callback_data="start")]
    ])
    await query.message.answer(
        "О чём вы сейчас думаете? Мы превратим любую мысль в уникальный проект!\n"
        "✍️ Просто введите текст ниже или \n"
        "🎲 могу предложить вам идею.\n\n"

        "⬇️⬇️⬇️ Пишите ⬇️⬇️⬇️",
        reply_markup=kb
    )
    await state.set_state(BrandCreationStates.waiting_for_context)


# 📍 Обработчик кнопки «Что это и зачем?»
@main_menu_router.callback_query(lambda c: c.data == "help")
async def show_help(query: types.CallbackQuery):
    await query.answer()  # Подтверждаем callback

    # Создаем кнопку "Вернуться в меню"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Вернуться в меню", callback_data="start")]
    ])

    await query.message.answer(
        "🧠 Этот генератор позволяет создать уникальный проект всего за 4 простых шага!\n\n"
        "💡 Уникальность подхода:\n"
        "1. Генератор проверяет свободность username в Telegram.\n"
        "2. Концепция проекта разрабатывается на основе ваших мыслей.\n"
        "3. Вы получаете готовый концепт, который можно сразу реализовать!\n\n"
        "🌟 Нажмите «Начать процесс», чтобы создать что-то уникальное прямо сейчас!\n",
        reply_markup=kb
    )
