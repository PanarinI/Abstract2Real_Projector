import os
from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = os.getenv("MODEL_NAME")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", 40))
TEMPERATURE_NAME = float(os.getenv("TEMPERATURE_NAME", "0.7"))

MODEL_BRAND= os.getenv("MODEL_BRAND")
MAX_TOKENS_BRAND = int(os.getenv("MAX_TOKENS_BRAND", 400))
TEMPERATURE_BRAND = float(os.getenv("TEMPERATURE_BRAND", "0.7"))

# Максимальное количество символов в контексте
MAX_CONTEXT_LENGTH = 200

# Количество итоговых доступных username, которое должно возвращаться
AVAILABLE_USERNAME_COUNT = 3

# Количество username, запрашиваемых у OpenAI за один раз
GENERATED_USERNAME_COUNT = int(os.getenv("GENERATED_USERNAME_COUNT"))

# Максимальное количество итераций (попыток) генерации username
GEN_ATTEMPTS = int(os.getenv("GEN_ATTEMPTS"))

# Максимальное общее время ожидания генерации (в секундах)
GEN_TIMEOUT = int(os.getenv("GEN_TIMEOUT"))  # Преобразуем в число

# Прерывание после нескольких пустых ответов
MAX_EMPTY_RESPONSES = 3

# Параметр для интервала между запросами (например, 1 секунда) -- способ избежать flood control exceeded
REQUEST_INTERVAL = 0.3



## генерация username
PROMPT_NO_STYLE = (
    "Создай {n} уникальных и разнообразных username для Telegram по теме '{context}'.\n"
    "Только если тема явно указывает на бота, добавь 'bot' или '_bot'.\n"
    "Используй только латинские буквы, цифры и нижнее подчёркивание (не в начале и не в конце).\n"
    "Длина username: от 5 до 32 символов.\n"
    "Сначала укажи только одну категорию темы (например, 'бизнес'), затем  на следующей строке список username через запятую."
)

PROMPT_TEST = (
    "Создай {n} уникальных и разнообразных username для Telegram по теме '{context}'.\n"
    "Только если тема явно указывает на бота, добавь 'bot' или '_bot'.\n"
    "Используй только латинские буквы. Цифры и символы (кроме подчёркивания) использовать только в исключительных случаях.\n"
    "Длина username: преимущественно от 6 до 15 символов.\n"
#   "Имена должны быть уникальными и не состоять из простых общеупотребительных слов, особенно если они короче 6 символов.\n"
    "Отдавай предпочтение осмысленным, но не слишком очевидным словам или их сочетаниям.\n"
)

PROMPT_WITH_STYLE = (
    "Создай {n} уникальных и разнообразных username для Telegram по теме '{context}', учитывая стиль '{style}'.\n"
    "Только если тема явно указывает на бота, добавь 'bot' или '_bot'.\n"
    "Используй только латинские буквы, цифры и нижнее подчёркивание (не в начале и не в конце).\n"
    "Длина username: от 5 до 32 символов.\n"
    "Сначала укажи только одну категорию темы (например, 'бизнес'), затем  на следующей строке список username через запятую."
)

STYLE_DESCRIPTIONS = {
    "epic": "мощные, звучные, внушительные username, которые вызывают ощущение силы и значимости",
    "strict": "строгие, лаконичные, солидные username, которые выглядят профессионально",
    "funky": "игривые, необычные, креативные username с элементами юмора",
    "minimal": "простые, элегантные, короткие username, которые выглядят стильно",
    "cringe": "абсурдные, нелепые, запоминающиеся username, которые могут выглядеть смешно или странно"
}

STYLE_TRANSLATIONS = {
    "epic": "эпичный",
    "strict": "строгий",
    "funky": "фанк",
    "minimal": "минимализм",
    "cringe": "кринж"
}



# Логирование
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")  # Читаем переменную из окружения, если нет — ставим INFO
LOG_FILE = "bot.log"  # Оставьте пустым "", если хотите логи только в консоль
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

