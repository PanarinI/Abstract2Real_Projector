import logging

from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.handlers.states import BrandCreationStates
from bot.handlers.main_menu import show_main_menu
from bot.services.brand_ask_ai import get_parsed_response



brand_router = Router()

GROUP_ID = -1002250762604  # ID твоей группы
THREAD_ID = 162  # Предполагаемый ID темы


def generate_message_and_keyboard(answer: str, options: list[dict], prefix: str) -> tuple[str, InlineKeyboardMarkup]:
    """
    Формирует текст сообщения и инлайн-кнопки с динамическим префиксом callback_data.

    :param answer: Текст комментария (подводка)
    :param options: Список вариантов (этапы 1, 2, 3)
    :param prefix: Префикс для callback_data (например, "choose_stage1", "choose_stage2", "choose_stage3")
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

    # Добавляем кнопку "Еще 3 варианта" в конец списка кнопок
    buttons.append([InlineKeyboardButton(text="🔄 Еще 3 варианта", callback_data="repeat_brand")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    return detailed_message, keyboard


# 📍 Этап 1: Какую проблему или потребность решает эта идея?
async def stage1_problem(event: types.Message | types.CallbackQuery, state: FSMContext):
    """
    Универсальная функция для Этапа 1, поддерживающая и Message, и CallbackQuery.
    """
    data = await state.get_data()
    username = data.get("username")
    context = data.get("context")  # Исходная идея пользователя

    if not username:
        await event.answer("❌ Ошибка: не передано имя проекта. Попробуйте снова.", reply_markup=back_to_menu_kb())
        await state.clear()
        return

    # Проверяем, есть ли контекст
    if not context:
        from bot.handlers.main_menu import back_to_menu_kb
        logging.warning("⚠️ Context отсутствует в FSM! Проверьте, передаётся ли он в начале.")
        await event.answer("❌ Ошибка: не удалось получить исходную концепцию. Начните заново.",
                           reply_markup=back_to_menu_kb())
        await state.clear()
        return

    # Определяем, какой метод использовать для отправки сообщений
    send_message = event.message.answer if isinstance(event, types.CallbackQuery) else event.answer

    # Отправляем сообщение пользователю перед генерацией
    await send_message("⏳ Думаю над ответом...")

    prompt = f"""
    Исходный контекст: {context}, выбрано название {username}.
    Проанализируй название и контекст с точки зрения смысловых ассоциаций и потенциального позиционирования.
    Какие 3 ключевые проблемы или потребности может решать проект, исходя из этой идеи?

    Ответ выведи строго по формату:
    Комментарий: [краткий комментарий к выбору {username} и подводящий вопрос. 1-2 предложения.]

    1. **[эмодзи]** [Проблема/Потребность 1]: [Описание]
    2. **[эмодзи]** [Проблема/Потребность 2]: [Описание]
    3. **[эмодзи]** [Проблема/Потребность 3]: [Описание]
    """

    parsed_response = get_parsed_response(prompt)

    if not parsed_response["options"]:
        await send_message("❌ Ошибка при генерации форматов. Попробуйте снова.")
        return

    await state.update_data(stage1_options=parsed_response["options"])

    # После получения parsed_response
    stage_text = "<b>Этап 1: суть.</b>\n"
    final_answer = stage_text + parsed_response["answer"]

    msg_text, kb = generate_message_and_keyboard(
        answer=final_answer,
        options=parsed_response["options"],
        prefix="choose_stage1"
    )

    kb.inline_keyboard.append([InlineKeyboardButton(text="🏠 Вернуться в меню", callback_data="start")])

    await send_message(msg_text, reply_markup=kb, parse_mode="HTML")
    await state.set_state(BrandCreationStates.waiting_for_stage1)


@brand_router.callback_query(lambda c: c.data.startswith("choose_stage1:"))
async def process_stage1(query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    stage1_options = data.get("stage1_options", [])
    index_str = query.data.split(":", 1)[1]

    try:
        index = int(index_str)
    except ValueError:
        await query.message.answer("❌ Ошибка: некорректный формат.")
        return

    if index < 0 or index >= len(stage1_options):
        await query.message.answer("❌ Ошибка: выбран некорректный формат.")
        return

    stage1_choice = stage1_options[index]
    await state.update_data(stage1_choice=stage1_choice)

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
    stage1_choice = data.get("stage1_choice")

    # Отправляем сообщение пользователю перед генерацией
    await query.message.answer("⏳ Думаю над ответом...")

    prompt = f"""
    Пользователь изначально указал: {context}.
    Пользователь выбрал название {username} и указал на проблему/потребность {stage1_choice}.
    Исходя из выявленной проблемы, с учетом контекста и выбранного названия предложи 3 варианта целевой аудитории, которая получит наибольшую выгоду от решения.
   
   
    Ответ выведи строго по формату:
    Комментарий: [краткий комментарий к выбору {stage1_choice} (отметь выбор в тексте) и краткий вопрос-подводка к вариантам. 1-2 предложения]
1. [эмодзи] [Название аудитории 1]: [Описание, почему именно эта аудитория заинтересована и какие выгоды она получит (1-2 предложения)]
2. [эмодзи] [Название аудитории 2]: [Описание, почему именно эта аудитория заинтересована и какие выгоды она получит (1-2 предложения)]
3. [эмодзи] [Название аудитории 3]: [Описание, почему именно эта аудитория заинтересована и какие выгоды она получит (1-2 предложения)]

    """
    #   Если ты отклонишься от формата — переделай ответ заново!
    parsed_response = get_parsed_response(prompt)

    if not parsed_response["options"]:
        await query.message.answer("❌ Ошибка при генерации аудитории. Попробуйте снова.")
        return

    await state.update_data(stage2_options=parsed_response["options"])

    stage_text = "<b>Этап 2: для кого?</b>\n"  # или любой другой формат, который вам нужен
    final_answer = stage_text + parsed_response["answer"]

    msg_text, kb = generate_message_and_keyboard(
        answer=final_answer,  # используем уже изменённый ответ
        options=parsed_response["options"],
        prefix="choose_stage2"
    )


    kb.inline_keyboard.append([InlineKeyboardButton(text="🏠 Вернуться в меню", callback_data="start")])
    await query.message.answer(msg_text, reply_markup=kb, parse_mode="HTML")
    await state.set_state(BrandCreationStates.waiting_for_stage2)


# 📍 Обработка выбора аудитории
@brand_router.callback_query(lambda c: c.data.startswith("choose_stage2:"))
async def process_stage2(query: types.CallbackQuery, state: FSMContext):
    """
    Обрабатывает выбор аудитории проекта пользователем.
    Сохраняет выбор в состоянии FSM и переходит к следующему этапу.
    """
    data = await state.get_data()
    stage2_options = data.get("stage2_options", [])
    index_str = query.data.split(":", 1)[1]

    try:
        index = int(index_str)
    except ValueError:
        await query.message.answer("❌ Ошибка: некорректная аудитория.")
        return

    if index < 0 or index >= len(stage2_options):
        await query.message.answer("❌ Ошибка: выбрана некорректная аудитория. Попробуйте снова.")
        return

    stage2_choice = stage2_options[index]
    await state.update_data(stage2_choice=stage2_choice)

    await query.answer()

    # Переход к следующему этапу (сути и ценности проекта)
    await stage3_shape(query, state)


# 📍 Этап 3: Каким образом можно конкретно реализовать эту идею, чтобы обеспечить её качественную ценность?
async def stage3_shape(query: types.CallbackQuery, state: FSMContext):
    """
    Генерирует варианты этапа 3 на основе контекста, username, проблемы и аудитории.
    Отправляет пользователю сообщение с комментарием и инлайн-кнопками выбора.
    """
    data = await state.get_data()
    username = data.get("username")
    context = data.get("context")
    stage1_choice = data.get("stage1_choice")
    stage2_choice = data.get("stage2_choice")

    # Отправляем сообщение пользователю перед генерацией
    await query.message.answer("⏳ Думаю над ответом...")

    prompt = f"""
    Исходный контекст: {context}, выбрано имя "{username}".
    Проблема/потребность "{stage1_choice}" и целевая аудитория "{stage2_choice}" (результаты предыдущих этапов).
    С учетом всего этого, какой конкретно можно реализовать проект, чтобы эффективно решать указанную проблему и приносить качественную ценность для аудитории?
    
    Ответ выведи строго по формату:
    Комментарий: [краткий комментарий к выбору {stage2_choice} (отметь выбор в тексте) и краткий вопрос-подводка к вариантам. 1-2 предложения]
    1. [эмодзи] [Краткое определение]: [1-2 предложения, поясняющие формат]
    2. [эмодзи] [Краткое определение]: [1-2 предложения, поясняющие формат]
    3. [эмодзи] [Краткое определение]: [1-2 предложения, поясняющие формат]
    """

    parsed_response = get_parsed_response(prompt)

    if not parsed_response["options"]:
        await query.message.answer("❌ Ошибка при генерации сути проекта. Попробуйте снова.")
        return

    await state.update_data(stage3_options=parsed_response["options"])

    # После получения parsed_response
    stage_text = "<b>Этап 3: формат</b>\n"  # или любой другой формат, который вам нужен
    final_answer = stage_text + parsed_response["answer"]

    msg_text, kb = generate_message_and_keyboard(
        answer=final_answer,  # используем уже изменённый ответ
        options=parsed_response["options"],
        prefix="choose_stage3"
    )

    kb.inline_keyboard.append([InlineKeyboardButton(text="🏠 Вернуться в меню", callback_data="start")])
    await query.message.answer(msg_text, reply_markup=kb, parse_mode="HTML")
    await state.set_state(BrandCreationStates.waiting_for_stage3)


# 📍 Обработка выбора Этапа 3
@brand_router.callback_query(lambda c: c.data.startswith("choose_stage3:"))
async def process_stage3_choice(query: types.CallbackQuery, state: FSMContext):
    """
    Обрабатывает выбор третьего этапа (формата проекта) и выводит финальный экран.
    """
    data = await state.get_data()
    stage3_options = data.get("stage3_options", [])
    index_str = query.data.split(":", 1)[1]

    try:
        index = int(index_str)
    except ValueError:
        await query.message.answer("❌ Ошибка: некорректный формат выбора.")
        return

    if index < 0 or index >= len(stage3_options):
        await query.message.answer("❌ Ошибка: выбран некорректный вариант формата.")
        return

    # Сохраняем выбранный объект (словарь с 'short' и 'full')
    stage3_choice = stage3_options[index]
    await state.update_data(stage3_choice=stage3_choice)

    await query.answer()

    # Вызываем функцию, которая выводит финальный экран (без отдельного декоратора)
    await show_final_profile(query, state)



async def show_final_profile(query: types.CallbackQuery, state: FSMContext):
    """
    Выводит сообщение с кнопкой "📜 Забрать проект", используя данные из состояния.
    """
    data = await state.get_data()
    username = data.get("username", "Неизвестный проект")
    # Здесь stage3_choice уже корректно сохранён как объект, поэтому не перезаписываем его:
    # stage3_choice = data.get("stage3_choice", {})  — и затем извлекаем short ниже.

    msg_text = f"✅ Проект <b>{username}</b> успешно собран!\nНажмите на кнопку ниже, чтобы забрать его."

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📜 Забрать проект", callback_data="get_project")],
            [InlineKeyboardButton(text="🏠 Вернуться в меню", callback_data="start")]
        ]
    )

    await query.message.answer(msg_text, reply_markup=keyboard, parse_mode="HTML")
    await state.set_state(BrandCreationStates.project_ready)


@brand_router.callback_query(lambda c: c.data == "get_project")
async def send_project_profile(query: types.CallbackQuery, state: FSMContext):
    """
    Отправляет пользователю полный профиль проекта после нажатия на "📜 Забрать проект".
    """
    data = await state.get_data()

    username = data.get("username")
    context = data.get("context")

    # Применяем ту же логику, что и для stage1_choice и stage2_choice
    stage1_choice = data.get("stage1_choice", {})
    stage2_choice = data.get("stage2_choice", {})
    stage3_choice = data.get("stage3_choice", {})

    if isinstance(stage1_choice, dict):
        stage1_choice = stage1_choice.get("short", "Не выбрано")
    if isinstance(stage2_choice, dict):
        stage2_choice = stage2_choice.get("short", "Не выбрано")
    if isinstance(stage3_choice, dict):
        stage3_choice = stage3_choice.get("short", "Не выбрано")

    # Отправляем сообщение пользователю перед генерацией
    await query.message.answer("⏳ Собираю всё вместе...")

    # Генерируем тэглайн и примеры существующих проектов
    prompt = f"""
    Пользователь создал концепцию проекта:
    - Мысль: {context}
    - Название: {username}
    - Проблема: {stage1_choice}
    - Аудитория: {stage2_choice}
    - Формат: {stage3_choice}
    
    Сформулируй:
    1. **Тэглайн проекта** – короткое, яркое описание его сути в 1 предложении.
    2. **3 реально существующих проекта** в этой сфере, с кратким описанием каждого.
    
    Учитывай изначальную мысль пользователя.
    Выведи результат в формате:
    Тэглайн: [короткое, яркое описание сути проекта одно предложение]
    [Краткое описание проекта в 2-3 предложения]

    Примеры похожих проектов:
    1. **[Название проекта]** – [1 предложение о сути и цели проекта]
    2. **[Название проекта]** – [1 предложение о сути и цели проекта]
    3. **[Название проекта]** – [1 предложение о сути и цели проекта]
    """

    parsed_response = get_parsed_response(prompt)
    tagline = parsed_response.get("answer", "Не удалось сгенерировать тэглайн.").replace("Тэглайн:", "").strip()
    references = parsed_response.get("options", [])

    # Формируем текст сообщения
    profile_text = f"""
📝 <b>Профиль проекта</b>

<b>{username}</b>  
<strong>{tagline}</strong>

<b>Концепция проекта:</b>
🔹 <b>Проблема:</b> {stage1_choice}  
🔹 <b>Аудитория:</b> {stage2_choice}  
🔹 <b>Формат:</b> {stage3_choice}  

<b>Похожие проекты:</b>
"""

    if references:
        for ref in references:
            profile_text += f"🔹 {ref['full']}\n"
    else:
        profile_text += "❌ Нет найденных похожих проектов.\n"

    profile_text += f"\n<i>{context}</i>"

    # **Создаём инлайн-клавиатуру**
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Вернуться в меню", callback_data="start")],
        [InlineKeyboardButton(text="📢 Поделиться проектом", callback_data="forward_project")],
        [InlineKeyboardButton(text="⭐ Оставить отзыв", callback_data="leave_feedback")]
    ])
    # Отправляем итоговый профиль
    await query.message.answer(profile_text, parse_mode="HTML", reply_markup=keyboard)

    # Очищаем состояние FSM
    await state.clear()


# Обработчик всех кнопкок "повторить"
@brand_router.callback_query(lambda c: c.data == "repeat_brand")
async def repeat_generation(query: types.CallbackQuery, state: FSMContext):
    await query.answer()  # Подтверждаем callback

    current_state = await state.get_state()

    if current_state == BrandCreationStates.waiting_for_stage1:
        await stage1_problem(query, state)

    elif current_state == BrandCreationStates.waiting_for_stage2:
        await stage2_audience(query, state)

    elif current_state == BrandCreationStates.waiting_for_stage3:
        await stage3_shape(query, state)

    else:
        await query.message.answer("❌ Неизвестное состояние. Попробуйте снова или начните с начала.")


@brand_router.callback_query(lambda c: c.data == "repeat_brand")
async def cmd_start_from_callback(query: types.CallbackQuery, state: FSMContext):
    await query.answer()  # Подтверждаем callback
    await state.clear()  # Очищаем состояние FSM

    # Вызываем универсальную функцию отображения главного меню
    await show_main_menu(query.message)


from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

FEEDBACK_CHAT_ID = -4770810793  # ID закрытой группы

# Храним оценки пользователей
user_ratings = {}

@brand_router.callback_query(lambda c: c.data == "leave_feedback")
async def request_feedback(query: types.CallbackQuery):
    """
    Шаг 1: Запросить у пользователя оценку (1-5 звёзд).
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [  # Первая строка
            InlineKeyboardButton(text="⭐", callback_data="rate_1"),
            InlineKeyboardButton(text="⭐⭐", callback_data="rate_2"),
            InlineKeyboardButton(text="⭐⭐⭐", callback_data="rate_3"),
        ],
        [  # Вторая строка
            InlineKeyboardButton(text="⭐⭐⭐⭐", callback_data="rate_4"),
            InlineKeyboardButton(text="⭐⭐⭐⭐⭐", callback_data="rate_5"),
        ]
    ])

    await query.message.answer("Оцените проект по шкале от 1 до 5 ⭐:", reply_markup=keyboard)


# Функция для отправки отзыва в закрытую группу
async def send_feedback_to_group(bot, rating: str, username: str, full_name: str, comment: str):
    feedback_text = (
        f"📩 <b>Новый отзыв!</b>\n\n"
        f"👤 <b>От:</b> @{username} ({full_name})\n"
        f"⭐ <b>Оценка:</b> {rating}/5\n\n"
        f"💬 <b>Отзыв:</b> {comment}"
    )
    # Отправляем отзыв в закрытую группу
    await bot.send_message(FEEDBACK_CHAT_ID, feedback_text, parse_mode="HTML")

# Обработчик для получения оценки пользователя
@brand_router.callback_query(lambda c: c.data.startswith("rate_"))
async def receive_rating(query: types.CallbackQuery, state: FSMContext):
    """
    Шаг 2: Получает оценку пользователя и предлагает оставить комментарий.
    """
    rating = query.data.split("_")[1]  # Получаем число от 1 до 5

    # Сохраняем оценку в состояние FSM
    await state.update_data(user_rating=rating)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Отправить без комментария", callback_data="skip_comment")]
    ])

    await query.message.answer(
        f"Спасибо за вашу оценку {rating}⭐!\nТеперь напишите ваш комментарий (по желанию) ⌨️",
        reply_markup=keyboard
    )

# Обработчик для пропуска комментария
@brand_router.callback_query(lambda c: c.data == "skip_comment")
async def skip_comment(query: types.CallbackQuery, state: FSMContext):
    """
    Шаг 3: Отправить отзыв без комментария и отправить в закрытую группу.
    """
    data = await state.get_data()
    rating = data.get("user_rating", "N/A")

    # Отправляем отзыв без комментария
    await send_feedback_to_group(query.bot, rating, query.from_user.username, query.from_user.full_name, "Нет комментария")

    # Благодарим пользователя
    await query.answer("Спасибо за ваш отзыв! 🎉")

    # Очищаем состояние FSM
    await state.clear()

    # Переходим в главное меню
    await show_main_menu(query.message)  # Переход к главному меню

# Функция для обработки отзыва с комментарием
@brand_router.message()
async def forward_feedback(message: types.Message, state: FSMContext):
    """
    Шаг 4: Получаем текст отзыва и отправляем его в закрытую группу.
    """
    if message.chat.type == "private":  # Проверяем, что сообщение пришло из личного чата
        data = await state.get_data()
        rating = data.get("user_rating", "N/A")

        # Если комментарий есть, используем его, иначе пишем "Нет комментария"
        comment = message.text if message.text else "Нет комментария"

        # Отправляем отзыв
        await send_feedback_to_group(message.bot, rating, message.from_user.username, message.from_user.full_name, comment)

        # Получаем callback_query для использования query.answer()
        query = await message.answer("Спасибо за ваш отзыв! 🎉")  # Отправляем сообщение благодарности


        # Очищаем состояние FSM
        await state.clear()

        # Переходим в главное меню
        await show_main_menu(message)  # Переход к главному меню



# Функция для обработки отзыва с комментарием или без
@brand_router.message()
async def forward_feedback(message: types.Message, state: FSMContext):
    """
    Шаг 4: Получаем текст отзыва и отправляем его в закрытую группу.
    """
    if message.chat.type == "private":  # Проверяем, что сообщение пришло из личного чата
        data = await state.get_data()
        rating = data.get("user_rating", "N/A")

        # Если отзыв с комментарием
        if message.text:
            feedback_text = (
                f"📩 <b>Новый отзыв!</b>\n\n"
                f"👤 <b>От:</b> @{message.from_user.username} ({message.from_user.full_name})\n"
                f"⭐ <b>Оценка:</b> {rating}/5\n\n"
                f"💬 <b>Отзыв:</b> {message.text}"
            )
        # Если отзыв без комментария
        else:
            feedback_text = (
                f"📩 <b>Новый отзыв!</b>\n\n"
                f"👤 <b>От:</b> @{message.from_user.username} ({message.from_user.full_name})\n"
                f"⭐ <b>Оценка:</b> {rating}/5\n\n"
                f"💬 <b>Отзыв:</b> Нет комментария"
            )

        # Отправляем отзыв в закрытую группу
        await message.bot.send_message(FEEDBACK_CHAT_ID, feedback_text, parse_mode="HTML")

        # Благодарим пользователя
        await message.answer("Спасибо за ваш отзыв! 🎉")

        # Очищаем состояние FSM
        await state.clear()

        # Переходим в главное меню, вызываем команду /start
        await show_main_menu(message)  # Вызываем команду start


@brand_router.callback_query(lambda c: c.data == "forward_project")
async def forward_project(query: types.CallbackQuery):
    """
    Пересылает последнее сообщение бота (профиль проекта) в указанную группу.
    """

    logging.info("🔄 Получен callback на пересылку проекта!")  # Логируем получение запроса

    try:
        # Пересылаем последнее сообщение от бота в группу
        forwarded_message = await query.message.forward(GROUP_ID, message_thread_id=THREAD_ID)

        # Отправляем пользователю уведомление
        await query.message.answer(
            f"✅ Проект успешно переслан в <a href='https://t.me/c/{str(GROUP_ID)[4:]}'><b>группу</b></a>!",
            parse_mode="HTML",
            disable_web_page_preview=True
        )

    except Exception as e:
        await query.message.answer(f"❌ Ошибка при пересылке: {e}")
