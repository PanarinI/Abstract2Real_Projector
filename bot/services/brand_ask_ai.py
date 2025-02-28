import os
import logging
from dotenv import load_dotenv
from openai import OpenAI
from bot import config
import re

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


# Парсер ответа от AI
def parse_ai_response(response: str) -> dict:
    parsed_data = {
        "answer": "",
        "options": []
    }

    if not response or not response.strip():
        logging.error("❌ Пустой ответ от AI передан в парсер!")
        return parsed_data

    lines = response.strip().split('\n')

    # Функция для очистки лишних символов форматирования
    def clean_text(text: str) -> str:
        # Убираем только символы форматирования, не трогая пробелы, дефисы и знаки препинания
        text = re.sub(r'(\*\*|__|[*_~`])', '', text)  # Удаляем **, __, *, _, ~, `
        text = re.sub(r'\[([^\[\]]+)\]', r'\1', text)  # Убираем квадратные скобки, оставляя содержимое
        text = re.sub(r'\s+', ' ', text)  # Сжимаем множественные пробелы в один
        return text.strip()

    for line in lines:
        line = clean_text(line.strip())
        if not line:
            continue

        # 1. Попытка извлечь комментарий по метке "Комментарий:"
        if not parsed_data["answer"] and (line.lower().startswith("комментарий:") or ":" not in line):
            if line.lower().startswith("комментарий:"):
                parsed_data["answer"] = line.split(":", 1)[1].strip()
            else:
                parsed_data["answer"] = line.strip()
            continue

        # 2. Извлечение вариантов ответа (если строка начинается с цифры и точки)
        if len(line) > 2 and line[0].isdigit() and line[1] == '.':
            option_body = line.split('.', 1)[1].strip()

            if ':' not in option_body:
                continue

            left_part, details = option_body.split(':', 1)
            left_part = left_part.strip()
            details = details.strip()

            segments = left_part.split(maxsplit=1)
            if len(segments) == 2:
                emoji, short_text = segments[0], segments[1]
            else:
                emoji, short_text = "", segments[0]

            emoji = clean_text(emoji).strip()
            short_text = clean_text(short_text).strip()

            # Собираем текст для кнопок и полного описания
            button_text = f"{emoji} {short_text}".strip()
            full_text = f"<b>{short_text}</b>: {details}"

            parsed_data["options"].append({
                "short": button_text,
                "full": full_text
            })

    # Если не найден комментарий
    if not parsed_data["answer"]:
        logging.error("❌ Парсер не нашел 'answer' в ответе AI!")
        parsed_data["answer"] = "Комментарий не найден. Проверьте ответ AI."

    if not parsed_data["options"]:
        logging.error("❌ Парсер не нашел 'options' в ответе AI!")
        parsed_data["options"] = [{
            "short": "Ошибка",
            "full": "Ошибка в генерации вариантов. Попробуйте снова."
        }]

    return parsed_data



# Обертка для вызова AI и парсинга ответа
def get_parsed_response(prompt: str) -> dict:
    """
    Отправляет запрос к AI, логирует сырой ответ, парсит и возвращает результат.
    """
    response = ask_ai(prompt)
    logging.info(f"Сырой ответ от AI: {response}")

    parsed = parse_ai_response(response)
    logging.info(f"Парсированный ответ: {parsed}")

    return parsed
