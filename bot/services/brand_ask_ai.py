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
            model=config.MODEL_BRAND,
            messages=[
                {"role": "system", "content": "Ты - талантливый и конструктивный разработчик проектов. "},
                {"role": "user", "content": prompt}
            ],
            max_tokens=config.MAX_TOKENS_BRAND,
            temperature=config.TEMPERATURE_BRAND,
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Ошибка при обращении к AI: {e}")
        return ""


# Парсер ответа от AI
import re
import logging

def parse_ai_response(response: str) -> dict:
    parsed_data = {
        "answer": "",
        "options": []
    }

    if not response or not response.strip():
        logging.error("❌ Пустой ответ от AI передан в парсер!")
        return parsed_data

    lines = response.strip().split('\n')

    def clean_text(text: str) -> str:
        """Удаляет лишние символы форматирования, но сохраняет ссылки и HTML."""
        text = re.sub(r'(\*\*|__|[*_~`])', '', text)  # Убираем жирный текст и курсив
        text = re.sub(r'\s+', ' ', text)  # Сжимаем пробелы
        return text.strip()

    def convert_markdown_links(text: str) -> str:
        """Конвертирует Markdown-ссылки [текст](URL) в HTML <a href="URL">текст</a>"""
        return re.sub(r'\[([^\]]+)\]\((https?://[^\)]+)\)', r'<a href="\2">\1</a>', text)

    for line in lines:
        line = clean_text(line.strip())
        if not line:
            continue

        # 1. Извлечение комментария (если это первая строка)
        if not parsed_data["answer"]:
            if "Комментарий:" in line:
                parsed_data["answer"] = convert_markdown_links(line.split("Комментарий:", 1)[1].strip())
            else:
                parsed_data["answer"] = convert_markdown_links(line.strip())
            continue

        # 2. Извлечение вариантов ответа: проверяем строки, начинающиеся с цифры и точки или с символа "•"
        if (len(line) > 2 and line[0].isdigit() and line[1] == '.') or line.startswith("•"):
            if line.startswith("•"):
                option_body = line[1:].strip()
            else:
                option_body = line.split('.', 1)[1].strip()

            # 💀 ОПАСНЫЙ МОМЕНТ: разделение по разделителю, который не встречается внутри слов
            separator_match = re.search(r'\s*[:\-—–|/\\>]\s+(?!\S*[-:]\S*)', option_body)

            if separator_match:
                separator = separator_match.group()
                left_part, details = option_body.split(separator, 1)
                left_part = left_part.strip()
                details = convert_markdown_links(details.strip())
            else:
                # Если разделитель не найден, пробуем обработать случай с эмодзи + жирный шрифт
                match = re.match(r'^(.*?)\s*\*\*(.*?)\*\*\s*:\s*(.*)$', option_body)
                if match:
                    emoji, short_text, details = match.groups()
                    left_part = f"{emoji} {short_text}".strip()
                    details = convert_markdown_links(details.strip())
                else:
                    parts = option_body.split()
                    left_part = parts[0] if parts else option_body
                    details = convert_markdown_links(" ".join(parts[1:]) if len(parts) > 1 else "Нет описания.")
            parsed_data["options"].append({
                "short": left_part,  # Краткое название, включая квадратные скобки, если они есть
                "full": f"<b>{left_part}</b>: {details}"  # Полный вариант с HTML-форматированием
            })

    # Если комментарий не найден, берём первую строку
    if not parsed_data["answer"] and lines:
        parsed_data["answer"] = convert_markdown_links(clean_text(lines[0].strip()))

    if not parsed_data["options"]:
        logging.error("❌ Парсер не нашел 'options' в ответе AI!")
        parsed_data["options"] = [{
            "short": "Ошибка",
            "full": "Ошибка в генерации вариантов. Попробуйте снова."
        }]

    return parsed_data





##

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
