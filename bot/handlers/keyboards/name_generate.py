import logging
import re

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def escape_md(text: str) -> str:
    """Экранирует спецсимволы для MarkdownV2"""
    if not text:
        return ""
    return re.sub(r'([_*[\]()~`>#+-=|{}.!@-])', r'\\\1', text)

def generate_username_kb(usernames: list, context: str, style: str = None, duration: float = 0.0) -> (
        str, InlineKeyboardMarkup):
    """
    Формирует текст сообщения и клавиатуру с кнопками, включая переход к созданию бренда
    """
    # Экранируем стиль, если он указан
    style_rus = f"в стиле *{escape_md(style)}*" if style else ""

    # Экранируем время выполнения
    time_prefix = f"\\[{escape_md(f'{duration:.2f}')} сек\\] "

    # Формируем текст сообщения с экранированием @
    message_text = (
            f"🎭 [{escape_md(f'{duration:.2f}')} сек] Вот уникальные имена на тему *{escape_md(context)}*:\n" +
            "\n".join([f"\\- @{escape_md(username)}" for username in usernames])
    )

    # Создаем клавиатуру с кнопками "Попробовать снова", "В меню" и "Создать бренд из имени"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Попробовать снова", callback_data="generate")],
        [InlineKeyboardButton(text="🔙 В меню", callback_data="back_to_main")],
        [InlineKeyboardButton(text="🆕 Создать бренд из имени", callback_data="create_brand")]
    ])

    return message_text, kb




def error_retry_kb() -> InlineKeyboardMarkup:
    """Клавиатура для ошибки: повторить генерацию или вернуться в главное меню."""
    kb_list = [
        [InlineKeyboardButton(text="🔄 Попробовать снова", callback_data="generate")],
        [InlineKeyboardButton(text="🔙 В меню", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb_list)


def initial_styles_kb():
    """Первый уровень меню: сразу сгенерировать или выбрать стиль"""
    buttons = [
        [InlineKeyboardButton(text="🎲 Приступить", callback_data="no_style")],
        [InlineKeyboardButton(text="🎭 Выбрать стиль", callback_data="choose_style")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def styles_kb():
    """Второй уровень меню: кнопки выбора стиля"""
    buttons = [
        [InlineKeyboardButton(text="🔥 Эпичный", callback_data="epic")],
        [InlineKeyboardButton(text="🎩 Строгий", callback_data="strict")],
        [InlineKeyboardButton(text="🎨 Фанковый", callback_data="funky")],
        [InlineKeyboardButton(text="⚪ Минималистичный", callback_data="minimal")],
        [InlineKeyboardButton(text="🤡 Кринжовый", callback_data="cringe")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main_style_menu")]
    ]
    logging.debug("генерируем кнопки")  # 🔍 Отладочный принт
    return InlineKeyboardMarkup(inline_keyboard=buttons)

