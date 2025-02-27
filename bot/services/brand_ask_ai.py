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


def parse_ai_response(response: str) -> dict:
    parsed_data = {
        "answer": "",  # Комментарий с подводкой
        "options": []  # Варианты форматов проекта
    }

    if not response:
        logging.error("❌ Пустой ответ от AI передан в парсер!")
        return parsed_data

    lines = response.strip().split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Извлекаем комментарий с подводкой
        if line.lower().startswith("комментарий:"):
            parsed_data["answer"] = line.split(":", 1)[1].strip()

        # Извлекаем варианты форматов
        elif line[0].isdigit() and line[1] == '.':
            option = line.split('.', 1)[1].strip()
            if option:
                parsed_data["options"].append(option)

    # Проверка на пустой ответ
    if not parsed_data["answer"]:
        logging.error("❌ Парсер не нашел 'answer' в ответе AI!")
        parsed_data["answer"] = "Комментарий не найден. Проверьте ответ AI."

    if not parsed_data["options"]:
        logging.error("❌ Парсер не нашел 'options' в ответе AI!")
        parsed_data["options"] = ["Ошибка в генерации вариантов. Попробуйте снова."]

    return parsed_data





