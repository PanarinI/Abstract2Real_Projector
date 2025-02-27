from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.handlers.states import BrandCreationStates

username_router = Router()


# 📍 Обработка введенной мысли пользователя
@username_router.message(BrandCreationStates.waiting_for_context)
async def process_user_thought(message: types.Message, state: FSMContext):
    user_thought = message.text.strip()
    await state.update_data(user_thought=user_thought)

    await message.answer("🔄 Генерируем варианты username на основе вашей мысли...")

    # 📍 Заглушка: подставляем тестовые username
    generated_usernames = [
        "ProjectIdeaBot",
        "UniqueConceptBot",
        "BrandCreatorBot"
    ]

    await state.update_data(username_options=generated_usernames)

    kb = InlineKeyboardMarkup(inline_keyboard=[
                                                  [InlineKeyboardButton(text=f"@{username}",
                                                                        callback_data=f"choose_username:{username}")]
                                                  for username in generated_usernames
                                              ] + [[InlineKeyboardButton(text="🔄 Повторить генерацию",
                                                                         callback_data="repeat_username_generation")]])

    await message.answer(
        "Выберите один из доступных username:",
        reply_markup=kb
    )
    await state.set_state(BrandCreationStates.waiting_for_username_choice)


# 📍 Обработка кнопки "Повторить генерацию"
@username_router.callback_query(lambda c: c.data == "repeat_username_generation")
async def repeat_username_generation(query: types.CallbackQuery, state: FSMContext):
    await query.answer()  # Подтверждаем callback
    await process_user_thought(query.message, state)


# 📍 Обработка выбора username
@username_router.callback_query(lambda c: c.data.startswith("choose_username:"))
async def process_username_choice(query: types.CallbackQuery, state: FSMContext):
    selected_username = query.data.split(":")[1]
    await state.update_data(username=selected_username)

    await query.answer()  # Подтверждаем callback

    # Вызываем функцию генерации бренда
    from bot.handlers.brand_gen import start_format_stage
    await start_format_stage(query, state)
