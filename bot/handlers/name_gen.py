import logging
import asyncio
import re
from datetime import datetime

from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Bot, Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from bot.handlers.keyboards.name_generate import escape_md
from services.name_gen import gen_process_and_check
from bot.handlers.keyboards.name_generate import generate_username_kb, error_retry_kb, initial_styles_kb, styles_kb
from .states import BrandCreationStates

import config

username_router = Router()

### ✅ 1. ОБРАБОТЧИК КНОПКИ "Сгенерировать username"
@username_router.callback_query(F.data == "generate")
async def cmd_generate_username(query: CallbackQuery, state: FSMContext):
    """
    Обработчик для кнопки "Сгенерировать username".
    """
    logging.info(f"📩 Нажата кнопка 'Сгенерировать username' от {query.from_user.username} (id={query.from_user.id})")

    await state.clear()  # Очищаем состояние перед новой командой
    await asyncio.sleep(0.05)  # ✅ Даем FSM время сброситься
    await state.update_data(start_time=datetime.now().isoformat())
    await query.message.answer(
        "🔭 О чём должно говорить имя? Напиши тему, и я поймаю три уникальных имени.\n"
        "<i>Например: «загадки истории», «космические котики», или что угодно — "
        '<a href="https://telegra.ph/Mogut-li-zakonchitsya-Telegram-imena-02-21">пространство имён бесконечно!</a></i>',
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=back_to_main_kb()
    )

    await state.set_state(BrandCreationStates.waiting_for_context)
    await query.answer()  # Telegram требует подтверждения, что callback обработан.


@username_router.message(Command("generate"))
async def cmd_generate_slash(message: types.Message, state: FSMContext):
    """
    Обработчик для команды /generate.
    """
    logging.info(f"📩 Команда /generate от {message.from_user.username} (id={message.from_user.id})")

    await state.clear()  # ⛔️ Принудительно очищаем ВСЕ состояния
    await asyncio.sleep(0.1)  # 🔄 Даём FSM время сброситься

    await message.answer("Введите тему/контекст для генерации username:", reply_markup=back_to_main_kb())
    await state.set_state(BrandCreationStates.waiting_for_context)


@username_router.message(BrandCreationStates.waiting_for_context)
async def process_context_input(message: types.Message, state: FSMContext):
    """
    Обработчик для введённого контекста. Теперь после ввода темы появляется 2 варианта:
    - Без выбора стиля (генерация сразу)
    - Выбрать стиль (открывает второе меню)
    """
    context_text = message.text.strip()
    logging.info(f"📝 Введён контекст: '{context_text}' (от {message.from_user.username}, id={message.from_user.id})")

    # ✅ Проверяем длину контекста
    if len(context_text) > config.MAX_CONTEXT_LENGTH:
        logging.warning(f"⚠️ Контекст слишком длинный ({len(context_text)} символов), обрезаем до {config.MAX_CONTEXT_LENGTH}.")
        await message.answer(f"⚠️ Контекст слишком длинный. Обрезаю до {config.MAX_CONTEXT_LENGTH} символов.")
        context_text = context_text[:config.MAX_CONTEXT_LENGTH]

    # ✅ Сохраняем контекст в FSM, чтобы использовать после выбора стиля
    await state.update_data(context=context_text)

    # ✅ Отправляем inline-клавиатуру с двумя вариантами
    await message.answer(
        "🎭 Как будем искать имя?",
        reply_markup=initial_styles_kb()  # Меню первого уровня
    )

    await state.set_state(BrandCreationStates.waiting_for_style)


@username_router.callback_query(BrandCreationStates.waiting_for_style)
async def process_style_choice(query: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Обрабатывает выбор стиля или генерацию без стиля.
    """
    selected_option = query.data

    if selected_option == "back_to_main_style_menu":
        await query.message.edit_reply_markup(reply_markup=initial_styles_kb())  # Меняем только клавиатуру
        await query.answer()
        return

    if selected_option == "choose_style":
        await query.message.edit_text(
            "🎭 Выбери стиль генерации:",
            reply_markup=styles_kb()
        )
        return

    elif selected_option == "no_style":
        await state.update_data(start_time=datetime.now().isoformat())
        progress_task = asyncio.create_task(send_progress_messages(query))
        await perform_username_generation(query, state, bot, style=None)
        progress_task.cancel()
        return

    # Обработка выбора конкретного стиля
    await state.update_data(start_time=datetime.now().isoformat())
    progress_task = asyncio.create_task(send_progress_messages(query))
    await perform_username_generation(query, state, bot, style=selected_option)
    progress_task.cancel()






def contains_cyrillic(text: str) -> bool:
    """Проверяет, есть ли в тексте кириллические символы."""
    return bool(re.search(r'[а-яА-Я]', text))


async def send_progress_messages(query: CallbackQuery):
    """Фоновая отправка сообщений о процессе генерации."""
    messages = [
        "Прислушиваюсь к цифровому эфиру...",
        "⏳..."
    ]

    for msg in messages:
        await asyncio.sleep(6)  # Задержка перед отправкой следующих сообщений
        try:
            logging.info(f"📤 Отправляем сообщение: {msg}")
            await query.message.answer(msg)
        except Exception as e:
            logging.error(f"❌ Ошибка при отправке сообщения о процессе генерации: {e}")
            break


async def perform_username_generation(query: CallbackQuery, state: FSMContext, bot: Bot, style: str | None):
    data = await state.get_data()
    context_text = data.get("context", "")
    start_time = data.get("start_time", "")

    if not start_time:
        logging.warning("⚠️ Внимание! start_time не найден в FSM. Установим текущее время.")
        start_time = datetime.now().isoformat()

    if not context_text:
        await query.message.answer("❌ Ошибка: не удалось получить тему генерации. Начните заново.", reply_markup=main_menu_kb())
        await state.clear()
        return

    logging.info(f"🚀 Генерация username: контекст='{context_text}', стиль='{style}'")

    await query.message.answer("⏳ Выслеживаю...")

    try:
        raw_usernames = await asyncio.wait_for(
            gen_process_and_check(bot, context_text, style, config.AVAILABLE_USERNAME_COUNT),
            timeout=config.GEN_TIMEOUT
        )
        usernames = [u.strip() for u in raw_usernames if u.strip()]

        if not usernames:
            logging.warning(f"❌ AI отказался генерировать username по этическим соображениям (контекст: '{context_text}', стиль: '{style}').")
            await query.message.answer(
                "❌ AI отказался генерировать имена по этическим соображениям. Попробуйте изменить запрос.",
                reply_markup=error_retry_kb()
            )
            await state.clear()
            return

        # Сохраняем сгенерированные usernames в FSM
        await state.update_data(usernames=usernames)
        await handle_generation_result(query, usernames, context_text, style, start_time)
        await state.set_state(BrandCreationStates.waiting_for_username_choice)

    except Exception as e:
        logging.error(f"❌ Ошибка генерации: {e}")
        await query.message.answer("❌ Ошибка при генерации. Попробуйте ещё раз.", reply_markup=error_retry_kb())
        await state.clear()


async def handle_generation_result(query: CallbackQuery, usernames: list[str], context: str, style: str | None, start_time: str):
    """
    Отправка результата генерации username пользователю.
    Вместо вывода простого сообщения, создаем кнопки для выбора username.
    """
    try:
        start_dt = datetime.fromisoformat(start_time)
    except ValueError:
        logging.error(f"❌ Ошибка: Некорректный формат start_time: '{start_time}'. Используем текущее время.")
        start_dt = datetime.now()

    duration = (datetime.now() - start_dt).total_seconds()

    # Формируем текст сообщения
    message_text = f"⏳ [{duration:.2f} сек] Вот уникальные имена на тему *{escape_md(context)}*:"

    # Создаем кнопки с username'ами
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"@{username}", callback_data=f"choose_username:{username}")]
        for username in usernames
    ])

    # Отправляем сообщение с кнопками выбора
    await query.message.answer(
        escape_md(message_text),  # 🛠️ Экранируем текст перед отправкой
        parse_mode="MarkdownV2",
        reply_markup=keyboard
    )

    logging.info("✅ Результаты генерации отправлены пользователю.")


# ★ ОБРАБОТЧИК ВЫБОРА USERNAME ★
@username_router.callback_query(lambda c: c.data.startswith("choose_username:"))
async def choose_username_handler(query: CallbackQuery, state: FSMContext):
    """
    Обработчик выбора username для создания бренда.
    Вместо отправки ссылки, сохраняем выбранный username и вызываем дальнейшую генерацию проекта.
    """
    await query.answer()

    # Получаем выбранный username из callback_data
    username = query.data.split(":", 1)[1]

    # Сохраняем выбранный username в состоянии FSM
    await state.update_data(username=username)
    logging.info(f"✅ Выбран username: {username}")

    # Вместо отправки ссылки переходим к следующему этапу генерации проекта
    from bot.handlers.brand_gen import start_format_stage
    await start_format_stage(query, state)

