import os
import logging
from dotenv import load_dotenv
from openai import OpenAI
from bot import config

# Загрузка переменных окружения
load_dotenv()

# Получение ключей API из окружения
API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL")

# Создание клиента OpenAI
client = OpenAI(api_key=API_KEY, base_url=BASE_URL)


# Функция для отправки запроса к AI
def ask_ai(prompt: str) -> str:
    try:
        response = client.chat.completions.create(
            model=config.MODEL,
            messages=[
                {"role": "system", "content": "Ты — креативный генератор идей и концепций."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=config.MAX_TOKENS,
            temperature=config.TEMPERATURE,
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Ошибка при обращении к AI: {e}")
        return ""


import logging
import re

def parse_ai_response(response: str) -> dict:
    """
    Парсит ответ AI на комментарий и варианты форматов.
    Возвращает словарь:
    {
      "answer": str,                # Комментарий (подводка)
      "options": [                  # Список вариантов
          {
              "short": str,         # Для кнопки (с пиктограммой)
              "full": str           # Для сообщения (без пиктограммы)
          },
          ...
      ]
    }
    """
    parsed_data = {
        "answer": "",
        "options": []
    }

    if not response or not response.strip():
        logging.error("❌ Пустой ответ от AI передан в парсер!")
        return parsed_data

    # Разделяем ответ на строки
    lines = response.strip().split('\n')

    # Функция для очистки лишних символов форматирования, если они встречаются
    def clean_text(text: str) -> str:
        # Убираем только спецсимволы форматирования, не трогая пробелы и пиктограммы
        return re.sub(r'[*_\-~`]+', '', text)

    for line in lines:
        line = clean_text(line.strip())
        if not line:
            continue

        # 1) Ищем комментарий
        # Пример строки: "Комментарий: Что-то короткое"
        if line.lower().startswith("комментарий:"):
            parsed_data["answer"] = line.split(":", 1)[1].strip()
            continue

        # 2) Ищем варианты, которые начинаются с цифры и точки, например: "1. 💡 Генератор идей: ..."
        # Условие, чтобы не вылететь с индекса
        if len(line) > 2 and line[0].isdigit() and line[1] == '.':
            # Удаляем "1." или "2." и т.д.
            option_body = line.split('.', 1)[1].strip()

            # Пример после split: "💡 Генератор идей: Интерактивная платформа..."
            # Убедимся, что есть двоеточие, чтобы разделить "краткое опред." и "подробности"
            if ':' not in option_body:
                continue

            left_part, details = option_body.split(':', 1)
            left_part = left_part.strip()
            details = details.strip()

            # Теперь нам нужно отделить пиктограмму от краткого определения.
            # Формат шаблона: [Пиктограмма] [Краткое определение]
            # Пример: "💡 Генератор идей"
            # Если нет плюса, используем логику с регулярным выражением,
            # либо вручную: отделяем первый «слово-эмодзи» от остального.

            # ПРИМЕР: left_part = "💡 Генератор идей"
            # Мы хотим: emoji="💡", short_text="Генератор идей"

            # Простейший подход: ищем первый пробел:
            # Но если AI вернет "💡  Генератор идей" с двойным пробелом, нужно учесть .split().
            segments = left_part.split(maxsplit=1)  # разбиваем максимум на 2 части
            if len(segments) == 2:
                emoji, short_text = segments[0], segments[1]
            else:
                # если AI не дал пробел, значит либо только пиктограмма, либо только определение
                emoji, short_text = "", segments[0]

            # Очищаем от лишних символов, если вдруг:
            emoji = clean_text(emoji).strip()
            short_text = clean_text(short_text).strip()

            # Form short & full
            # short -> для кнопки, включает пиктограмму
            button_text = f"{emoji} {short_text}".strip()

            # full -> без пиктограммы, в bold краткое определение + подробности
            full_text = f"<b>{short_text}</b>: {details}"

            parsed_data["options"].append({
                "short": button_text,
                "full": full_text
            })

    # Если не нашли комментарий:
    if not parsed_data["answer"]:
        logging.error("❌ Парсер не нашел 'answer' в ответе AI!")
        parsed_data["answer"] = "Комментарий не найден. Проверьте ответ AI."

    # Если не нашли варианты:
    if not parsed_data["options"]:
        logging.error("❌ Парсер не нашел 'options' в ответе AI!")
        parsed_data["options"] = [{
            "short": "Ошибка",
            "full": "Ошибка в генерации вариантов. Попробуйте снова."
        }]

    return parsed_data





