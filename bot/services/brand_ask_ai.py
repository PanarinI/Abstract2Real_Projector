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
def parse_ai_response(response: str) -> dict:
    parsed_data = {
        "answer": "",  # Сюда будет попадать тэглайн или старый комментарий
        "description": "",  # Новое поле для описания проекта
        "options": []  # Примеры проектов или варианты
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

    # Ищем тэглайн и описание в первых строках
    tagline = None
    description = None
    remaining_lines = []

    for i, line in enumerate(lines):
        cleaned_line = clean_text(line.strip())
        if not cleaned_line:
            continue

        if cleaned_line.startswith("Тэглайн:"):
            tagline = convert_markdown_links(cleaned_line.split("Тэглайн:", 1)[1].strip())
        elif cleaned_line.startswith("Описание:"):
            description = convert_markdown_links(cleaned_line.split("Описание:", 1)[1].strip())
        else:
            remaining_lines.append(cleaned_line)

    # Если найден новый формат (есть тэглайн и описание)
    if tagline or description:
        parsed_data["answer"] = tagline or ""
        parsed_data["description"] = description or ""

        # Обрабатываем примеры проектов
        for line in remaining_lines:
            if not line or line.startswith("Примеры похожих проектов:"):
                continue

            # Обработка пунктов списка
            if re.match(r'^(\d+\.|•)\s*', line):
                # Удаляем маркеры списка
                clean_line = re.sub(r'^(\d+\.|•)\s*', '', line)

                # Удаляем слова "Проблема 1", "Проблема 2" и т.д.
                clean_line = re.sub(r'^Проблема\s*\d+:\s*', '', clean_line)

                # Разделяем на название и описание
                parts = re.split(r'\s*[:\-—–|/\\>]\s+', clean_line, 1)
                if len(parts) == 2:
                    name, desc = parts
                    parsed_data["options"].append({
                        "short": convert_markdown_links(name.strip()),  # Только эмодзи + название
                        "full": f"<b>{convert_markdown_links(name.strip())}</b>: {convert_markdown_links(desc.strip())}"  # Полный текст
                    })
                else:
                    parsed_data["options"].append({
                        "short": convert_markdown_links(clean_line.strip()),  # Только эмодзи + название
                        "full": convert_markdown_links(clean_line.strip())  # Полный текст
                    })

    # Если новый формат не найден, обрабатываем старый формат
    else:
        for line in lines:
            line = clean_text(line.strip())
            if not line:
                continue

            if not parsed_data["answer"]:
                if "Комментарий:" in line:
                    parsed_data["answer"] = convert_markdown_links(line.split("Комментарий:", 1)[1].strip())
                else:
                    parsed_data["answer"] = convert_markdown_links(line.strip())
                continue

            # Обработка вариантов (старый формат)
            if (len(line) > 2 and line[0].isdigit() and line[1] == '.') or line.startswith("•"):
                if line.startswith("•"):
                    option_body = line[1:].strip()
                else:
                    option_body = line.split('.', 1)[1].strip()

                # Удаляем слова "Проблема 1", "Проблема 2" и т.д.
                option_body = re.sub(r'^Проблема\s*\d+:\s*', '', option_body)

                # Разделение по разделителю, который не встречается внутри слов
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