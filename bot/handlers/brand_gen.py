import logging

from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from .states import BrandCreationStates
from bot.handlers.main_menu import show_main_menu
from bot.services.brand_ask_ai import get_parsed_response



brand_router = Router()

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def generate_message_and_keyboard(answer: str, options: list[dict], prefix: str) -> tuple[str, InlineKeyboardMarkup]:
    """
    Формирует текст сообщения и инлайн-кнопки с динамическим префиксом callback_data.

    :param answer: Текст комментария (подводка)
    :param options: Список вариантов (форматы, аудитория, ценность)
    :param prefix: Префикс для callback_data (например, "choose_format", "choose_audience", "choose_value")
    :return: Кортеж (текст сообщения, клавиатура)
    """

    # Формируем текст сообщения с комментариями и вариантами
    detailed_message = f"<b>Комментарий:</b>\n{answer}\n\n<b>Варианты:</b>\n"
    for opt in options:
        detailed_message += f"• {opt['full']}\n"

    # Создаем инлайн-кнопки с динамическим префиксом
    buttons = [
        [InlineKeyboardButton(text=opt['short'], callback_data=f"{prefix}:{i}")]
        for i, opt in enumerate(options)
    ]

    # Добавляем кнопку "Повторить" в конец списка кнопок
    buttons.append([InlineKeyboardButton(text="🔄 Повторить", callback_data="repeat_brand")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    return detailed_message, keyboard


# 📍 Этап 1: Выбор формата проекта
async def stage1_problem(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    username = data.get("username")
    context = data.get("context")  # Исходная идея пользователя
    if not context:
        logging.warning("⚠️ Context отсутствует в FSM! Проверьте, передаётся ли он в начале.")
        await query.message.answer("❌ Ошибка: не удалось получить исходную концепцию. Начните заново.",
                                   reply_markup=error_retry_kb())
        await state.clear()
        return

    prompt = f"""
    Исходный контекст: {context}, выбрано название {username}.
    Проанализируй имя и контекст с точки зрения смысловых ассоциаций и потенциального позиционирования.
    Какие 3 ключевые проблемы или потребности может решать проект, исходя из этой идеи?

    Комментарий: [краткий комментарий к выбору {username} и подводязий вопрос. 1-2 предложения]
    Пиши кратко.
    1. **[эмодзи]** [Проблема/Потребность 1]: [Описание того, как данное решение отвечает на проблему (1-2 предложения)]
    2. **[эмодзи]** [Проблема/Потребность 2]: [Описание того, как данное решение отвечает на проблему (1-2 предложения)]
    3. **[эмодзи]** [Проблема/Потребность 3]: [Описание того, как данное решение отвечает на проблему (1-2 предложения)]
    """

    parsed_response = get_parsed_response(prompt)

    if not parsed_response["options"]:
        await query.message.answer("❌ Ошибка при генерации форматов. Попробуйте снова.")
        return

    await state.update_data(format_options=parsed_response["options"])

    # Генерируем текст сообщения и клавиатуру
    msg_text, kb = generate_message_and_keyboard(
        answer=parsed_response["answer"],
        options=parsed_response["options"],
        prefix="choose_format"
    )

    await query.message.answer(msg_text, reply_markup=kb, parse_mode="HTML")
    await state.set_state(BrandCreationStates.waiting_for_format)


@brand_router.callback_query(lambda c: c.data.startswith("choose_format:"))
async def process_stage1(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    format_options = data.get("format_options", [])
    index_str = query.data.split(":", 1)[1]

    try:
        index = int(index_str)
    except ValueError:
        await query.message.answer("❌ Ошибка: некорректный формат.")
        return

    if index < 0 or index >= len(format_options):
        await query.message.answer("❌ Ошибка: выбран некорректный формат.")
        return

    problem_choice = format_options[index]
    await state.update_data(problem_choice=problem_choice)

    await query.answer()

    # Переход к следующему этапу
    from handlers.brand_gen import stage2_audience
    await stage2_audience(query, state)


# 📍 Этап 2: Определение аудитории проекта
async def stage2_audience(query: types.CallbackQuery, state: FSMContext):
    """
    Генерирует варианты направлений развития проекта и целевую аудиторию.
    Отправляет пользователю сообщение с комментариями и инлайн-кнопками выбора.
    """
    data = await state.get_data()
    username = data.get("username")
    context = data.get("context")
    problem_choice = data.get("problem_choice")

    prompt = f"""
    Пользователь изначально указал: {context}.
    Пользователь выбрал имя {username} и указал на проблему/потребность {problem_choice}.
    Исходя из выявленной проблемы, предложи 3 варианта целевой аудитории, которая получит наибольшую выгоду от решения.

    Комментарий: [краткий комментарий к выбору {problem_choice} (привести выбор в тексте) и краткий вопрос-подводка к вариантам. 1-2 предложения]
1. [эмодзи] [Название аудитории 1]: [Описание, почему именно эта аудитория заинтересована и какие выгоды она получит (1-2 предложения)]
2. [эмодзи] [Название аудитории 2]: [Описание, почему именно эта аудитория заинтересована и какие выгоды она получит (1-2 предложения)]
3. [эмодзи] [Название аудитории 3]: [Описание, почему именно эта аудитория заинтересована и какие выгоды она получит (1-2 предложения)]

    """
    #   Если ты отклонишься от формата — переделай ответ заново!
    parsed_response = get_parsed_response(prompt)

    if not parsed_response["options"]:
        await query.message.answer("❌ Ошибка при генерации аудитории. Попробуйте снова.")
        return

    await state.update_data(audience_options=parsed_response["options"])

    # Генерация сообщения и клавиатуры
    msg_text, kb = generate_message_and_keyboard(
        answer=parsed_response["answer"],
        options=parsed_response["options"],
        prefix="choose_audience"
    )

    await query.message.answer(msg_text, reply_markup=kb, parse_mode="HTML")
    await state.set_state(BrandCreationStates.waiting_for_audience)


# 📍 Обработка выбора аудитории
@brand_router.callback_query(lambda c: c.data.startswith("choose_audience:"))
async def process_stage2(query: types.CallbackQuery, state: FSMContext):
    """
    Обрабатывает выбор аудитории проекта пользователем.
    Сохраняет выбор в состоянии FSM и переходит к следующему этапу.
    """
    data = await state.get_data()
    audience_options = data.get("audience_options", [])
    index_str = query.data.split(":", 1)[1]

    try:
        index = int(index_str)
    except ValueError:
        await query.message.answer("❌ Ошибка: некорректная аудитория.")
        return

    if index < 0 or index >= len(audience_options):
        await query.message.answer("❌ Ошибка: выбрана некорректная аудитория. Попробуйте снова.")
        return

    audience_choice = audience_options[index]
    await state.update_data(audience_choice=audience_choice)

    await query.answer()

    # Переход к следующему этапу (сути и ценности проекта)
    await start_value_stage(query, state)


# 📍 Этап 3: Каким образом можно конкретно реализовать эту идею, чтобы обеспечить её качественную ценность?
async def start_value_stage(query: types.CallbackQuery, state: FSMContext):
    """
    Генерирует варианты этапа 3 на основе контекста, username, проблемы и аудитории.
    Отправляет пользователю сообщение с комментариями и инлайн-кнопками выбора.
    """
    data = await state.get_data()
    username = data.get("username")
    context = data.get("context")
    problem_choice = data.get("problem_choice")
    audience_choice = data.get("audience_choice")

    prompt = f"""
    Исходный контекст: {context}, выбрано имя "{username}".
    Проблема/потребность "{problem_choice}" и целевая аудитория "{audience_choice}" (результаты предыдущих этапов).
    Как можно конкретно реализовать проект, чтобы эффективно решать указанную проблему и приносить качественную ценность для аудитории?
    
    Комментарий: [краткий комментарий к выбору {audience_choice} (озвучить выбор) и краткий вопрос-подводка к вариантам. 1-2 предложения]
    1. [эмодзи] [Краткое определение]: [1-2 предложения, поясняющие формат]
    2. [эмодзи] [Краткое определение]: [1-2 предложения, поясняющие формат]
    3. [эмодзи] [Краткое определение]: [1-2 предложения, поясняющие формат]
    """

    parsed_response = get_parsed_response(prompt)

    if not parsed_response["options"]:
        await query.message.answer("❌ Ошибка при генерации сути проекта. Попробуйте снова.")
        return

    await state.update_data(value_options=parsed_response["options"])

    # Генерация сообщения и клавиатуры
    msg_text, kb = generate_message_and_keyboard(
        answer=parsed_response["answer"],
        options=parsed_response["options"],
        prefix="choose_value"
    )

    await query.message.answer(msg_text, reply_markup=kb, parse_mode="HTML")
    await state.set_state(BrandCreationStates.waiting_for_value)


# 📍 Обработка выбора сути и ценности проекта
@brand_router.callback_query(lambda c: c.data.startswith("choose_value:"))
async def process_value_choice(query: types.CallbackQuery, state: FSMContext):
    """
    Обрабатывает выбор сути и ценности проекта пользователем.
    Сохраняет выбор в состоянии FSM и завершает процесс создания профиля бренда.
    """
    data = await state.get_data()
    value_options = data.get("value_options", [])
    index_str = query.data.split(":", 1)[1]

    try:
        index = int(index_str)
    except ValueError:
        await query.message.answer("❌ Ошибка: некорректная ценность проекта.")
        return

    if index < 0 or index >= len(value_options):
        await query.message.answer("❌ Ошибка: выбрана некорректная ценность проекта. Попробуйте снова.")
        return

    value_choice = value_options[index]
    await state.update_data(value_choice=value_choice)

    await query.answer()

    # Завершение процесса и вывод финального профиля бренда
    await show_final_profile(query, state)


@brand_router.callback_query(lambda c: c.data.startswith("choose_value:"))
async def show_final_profile(query: types.CallbackQuery, state: FSMContext):
    """
    Формирует итоговый профиль бренда на основе всех выбранных параметров.
    Отправляет финальное сообщение пользователю с кнопками "Вернуться в меню",
    "Поделиться впечатлениями" и "Мастерская Бот и Кот".
    """
    value_choice = query.data.split(":")[1]
    await state.update_data(value_choice=value_choice)

    data = await state.get_data()
    profile_text = f"""
    📝 Профиль бренда:
    - Username: {data['username']}
    - Формат: {data['problem_choice']}
    - Аудитория: {data['audience_choice']}
    - Суть и ценность: {data['value_choice']}
    """

    # Создаем кнопки для финального сообщения
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Вернуться в меню", callback_data="start")],
        [InlineKeyboardButton(text="📝 Поделиться впечатлениями", url="https://example.com/feedback-form")],
    ])

    await query.message.answer(profile_text, reply_markup=kb)
    await state.clear()


# Обработчик всех кнопкок "вернуться назад"
@brand_router.callback_query(lambda c: c.data == "repeat_brand")
async def repeat_generation(query: types.CallbackQuery, state: FSMContext):
    await query.answer()  # Подтверждаем callback

    current_state = await state.get_state()

    if current_state == BrandCreationStates.waiting_for_format:
        await stage1_problem(query, state)

    elif current_state == BrandCreationStates.waiting_for_audience:
        await stage2_audience(query, state)

    elif current_state == BrandCreationStates.waiting_for_value:
        await start_value_stage(query, state)

    else:
        await query.message.answer("❌ Неизвестное состояние. Попробуйте снова или начните с начала.")


@brand_router.callback_query(lambda c: c.data == "repeat_brand")
async def cmd_start_from_callback(query: types.CallbackQuery, state: FSMContext):
    await query.answer()  # Подтверждаем callback
    await state.clear()  # Очищаем состояние FSM

    # Вызываем универсальную функцию отображения главного меню
    await show_main_menu(query.message)
