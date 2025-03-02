from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import logging
import re

def escape_md(text: str) -> str:
    """Экранирует спецсимволы для MarkdownV2"""
    if not text:
        return ""
    return re.sub(r'([_*[\]()~`>#+-=|{}.!@-])', r'\\\1', text)


def generate_username_kb(usernames: list[str], context: str, style: str = None, duration: float = 0.0) -> tuple[str, InlineKeyboardMarkup]:
    """
    Формирует текст сообщения и клавиатуру с кнопками, включая переход к созданию бренда.
    """
    style_rus = f"в стиле *{escape_md(style)}*" if style else ""
    duration_str = f"{duration:.2f}".replace('.', '\\.')
    time_prefix = f"\\[{duration_str} сек\\] "

    # 🔥 Формируем текст сообщения
    message_text = (
        f"🎭 {time_prefix}Выберите одно из уникальных имён на тему *{escape_md(context)}*\n\n"
    )

    # 🔹 **Генерируем кнопки для выбора username**
    buttons = [[InlineKeyboardButton(text=f"@{username}", callback_data=f"choose_username:{username}")]
               for username in usernames]

    # 🔹 **Добавляем кнопки "Еще 3 варианта" и "В меню"**
    buttons.append([InlineKeyboardButton(text="🔄 Еще 3 варианта", callback_data="repeat")])
    buttons.append([InlineKeyboardButton(text="🔙 В меню", callback_data="start")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    return message_text, keyboard





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

