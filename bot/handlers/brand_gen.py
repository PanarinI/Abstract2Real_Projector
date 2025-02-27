import logging

from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from .states import BrandCreationStates
from bot.handlers.main_menu import show_main_menu
from bot.services.brand_ask_ai import ask_ai, parse_ai_response



brand_router = Router()

#автоматический перенос текста ответа в кнопках
def split_text_to_two_lines(text: str, max_length: int = 30) -> str:
    """
    Разбивает текст на две строки, не превышая max_length символов на строку.
    """
    if len(text) <= max_length:
        return text

    # Находим ближайший пробел к границе строки, чтобы не обрывать слова
    space_index = text.rfind(' ', 0, max_length)

    if space_index == -1:
        # Если пробела нет, принудительно разрезаем текст
        return f"{text[:max_length]}\n{text[max_length:]}"

    # Разбиваем текст на две строки по пробелу
    return f"{text[:space_index]}\n{text[space_index + 1:]}"


# 📍 Этап 1: Выбор формата проекта
async def start_format_stage(query: types.CallbackQuery, state: FSMContext):
    """
    Генерирует варианты форматов проекта на основе выбранного username.
    Отправляет пользователю сообщение с комментариями и инлайн-кнопками выбора.
    """
    data = await state.get_data()
    username = data.get("username")

    prompt = f"""
    Пользователь выбрал username "{username}".
    Проанализируй "{username}" с точки зрения смысла, ассоциаций и контекстов.
    Предложи 3 чётких варианта того, в каком формате может реализоваться бренд.

    Ответ верни в следующем формате (не больше 12-15 слов на комментарий и каждый из вариантов):

    Комментарий: [краткий комментарий к выбору {username} и краткая подводка к вариантам - 1 предложение]
    1. [Вариант один]
    2. [Вариант два]
    3. [Вариант три]
    
    Каждый вариант - в формате: пиктограмма + краткое и конкретное определение + ":" + подробности в одном предложении, раскрывающие суть]
    """

    response = ask_ai(prompt)
    parsed_response = parse_ai_response(response)

    if not parsed_response["answer"]:
        await query.message.answer("❌ Ошибка: пустое сообщение от AI. Попробуйте снова.")
        logging.error(f"❌ Пустое сообщение от AI: {response}")
        return

    if not parsed_response["options"]:
        await query.message.answer("❌ Ошибка при генерации форматов. Попробуйте снова.")
        logging.error(f"❌ Ошибка парсинга опций: {response}")
        return

    await state.update_data(format_options=parsed_response["options"])

    # Вместо полного текста в callback_data передаем индекс варианта
    kb = InlineKeyboardMarkup(inline_keyboard=[
      [InlineKeyboardButton(text=split_text_to_two_lines(option, 30), callback_data=f"choose_format:{index}")]
      for index, option in enumerate(parsed_response["options"])
    ] + [[InlineKeyboardButton(text="🔄 Повторить", callback_data="repeat")]])

    await query.message.answer(parsed_response["answer"], reply_markup=kb)
    await state.set_state(BrandCreationStates.waiting_for_format)


@brand_router.callback_query(lambda c: c.data.startswith("choose_format:"))
async def process_format_choice(query: types.CallbackQuery, state: FSMContext):
    """
    Обрабатывает выбор формата проекта пользователем.
    Сохраняет выбор в состоянии FSM и переходит к следующему этапу.
    """
    data = await state.get_data()
    format_options = data.get("format_options", [])
    index = int(query.data.split(":", 1)[1])

    if index < 0 or index >= len(format_options):
        await query.message.answer("❌ Ошибка: выбран некорректный формат. Попробуйте снова.")
        return

    format_choice = format_options[index]
    await state.update_data(format_choice=format_choice)

    await query.answer()
    from handlers.brand_gen import start_audience_stage
    await start_audience_stage(query, state)




# 📍 Этап 2: Определение аудитории проекта
async def start_audience_stage(query: types.CallbackQuery, state: FSMContext):
    """
    Генерирует варианты направлений развития проекта и целевую аудиторию.
    Отправляет пользователю сообщение с комментариями и инлайн-кнопками выбора.
    """
    data = await state.get_data()
    username = data.get("username")
    format_choice = data.get("format_choice")

    prompt = f"""
    Пользователь выбрал имя "{username}".
    Пользователь выбрал формат "{format_choice}".
    Предложи 3 варианта того, в каком направлении 
    может развиваться проект "{username}". Кто будет этим пользоваться?
    
    Ответ верни в следующем формате (не больше 12-15 слов на комментарий и каждый из вариантов):

    Комментарий: [краткий комментарий к выбору {format_choice} и краткая подводка к вариантам - 1 предложение]
    1. [Вариант один]
    2. [Вариант два]
    3. [Вариант три]
    
    Каждый вариант - в формате: пиктограмма + краткое и конкретное определение + ":" + подробности в одном предложении, раскрывающие суть]
    """

    response = ask_ai(prompt)
    parsed_response = parse_ai_response(response)

    if not parsed_response["options"]:
        await query.message.answer("❌ Ошибка при генерации аудитории. Попробуйте снова.")
        return

    await state.update_data(audience_options=parsed_response["options"])

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=option, callback_data=f"choose_audience:{index}")]
        for index, option in enumerate(parsed_response["options"])
    ] + [[InlineKeyboardButton(text="🔄 Повторить", callback_data="repeat")]])

    await query.message.answer(parsed_response["answer"], reply_markup=kb)
    await state.set_state(BrandCreationStates.waiting_for_audience)


# 📍 Обработка выбора аудитории
@brand_router.callback_query(lambda c: c.data.startswith("choose_audience:"))
async def process_audience_choice(query: types.CallbackQuery, state: FSMContext):
    """
    Обрабатывает выбор аудитории проекта пользователем.
    Сохраняет выбор в состоянии FSM и переходит к следующему этапу.
    """
    data = await state.get_data()
    audience_options = data.get("audience_options", [])
    index = int(query.data.split(":", 1)[1])

    if index < 0 or index >= len(audience_options):
        await query.message.answer("❌ Ошибка: выбрана некорректная аудитория. Попробуйте снова.")
        return

    audience_choice = audience_options[index]
    await state.update_data(audience_choice=audience_choice)
    logging.info(f"✅ Пользователь выбрал аудиторию проекта: {audience_choice}")

    await start_value_stage(query, state)



# 📍 Этап 3: Определение сути и ценности проекта
async def start_value_stage(query: types.CallbackQuery, state: FSMContext):
    """
    Генерирует варианты сути и ценности проекта на основе выбранных username, формата и аудитории.
    Отправляет пользователю сообщение с комментариями и инлайн-кнопками выбора.
    """
    data = await state.get_data()
    username = data.get("username")
    format_choice = data.get("format_choice")
    audience_choice = data.get("audience_choice")

    prompt = f"""
    Пользователь выбрал имя "{username}".
    Пользователь выбрал формат "{format_choice}" и его направление "{audience_choice}".
    Предложи 3 варианта сути и ценности проекта.
        
    Ответ верни в следующем формате (не больше 12-15 слов на комментарий и каждый из вариантов):

    Комментарий: [краткий комментарий к выбору {audience_choice} и подводка к вопросу (1 предложение)]
    1. [Вариант один]
    2. [Вариант два]
    3. [Вариант три]
    
    Каждый вариант - в формате: пиктограмма + краткое и конкретное определение + ":" + подробности в одном предложении, раскрывающие суть]
    """

    response = ask_ai(prompt)
    parsed_response = parse_ai_response(response)

    if not parsed_response["options"]:
        await query.message.answer("❌ Ошибка при генерации сути проекта. Попробуйте снова.")
        return

    await state.update_data(value_options=parsed_response["options"])

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=option, callback_data=f"choose_value:{index}")]
        for index, option in enumerate(parsed_response["options"])
    ] + [[InlineKeyboardButton(text="🔄 Повторить", callback_data="repeat")]])

    await query.message.answer(parsed_response["answer"], reply_markup=kb)
    await state.set_state(BrandCreationStates.waiting_for_value)


@brand_router.callback_query(lambda c: c.data.startswith("choose_value:"))
async def final_stage(query: types.CallbackQuery, state: FSMContext):
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
    - Формат: {data['format_choice']}
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
@brand_router.callback_query(lambda c: c.data == "repeat")
async def repeat_generation(query: types.CallbackQuery, state: FSMContext):
    await query.answer()  # Подтверждаем callback

    current_state = await state.get_state()

    if current_state == BrandCreationStates.waiting_for_format:
        await start_format_stage(query, state)

    elif current_state == BrandCreationStates.waiting_for_audience:
        await start_audience_stage(query, state)

    elif current_state == BrandCreationStates.waiting_for_value:
        await start_value_stage(query, state)

    else:
        await query.message.answer("❌ Неизвестное состояние. Попробуйте снова или начните с начала.")


@brand_router.callback_query(lambda c: c.data == "start")
async def cmd_start_from_callback(query: types.CallbackQuery, state: FSMContext):
    await query.answer()  # Подтверждаем callback
    await state.clear()  # Очищаем состояние FSM

    # Вызываем универсальную функцию отображения главного меню
    await show_main_menu(query.message)
