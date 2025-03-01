import asyncio
import logging
import re
import aiohttp
import ssl
from bs4 import BeautifulSoup
from database.database import save_username_to_db  # Импорт здесь, чтобы избежать циклических импортов


async def check_multiple_usernames(usernames: list[str], save_to_db: bool = False) -> dict:
    """
    Проверяет список username параллельно.
    Возвращает словарь {username: статус}.
    """
    async with aiohttp.ClientSession() as session:
        tasks = [check_username_via_fragment(session, username) for username in usernames]
        results = await asyncio.gather(*tasks)

    availability = dict(zip(usernames, results))

    if save_to_db: # если запущена не генерация, а отдельная проверка
        tasks = [
            save_username_to_db(username=username, status=status, category="Пользовательская проверка",
                                context="Ручная проверка", llm="none")
            for username, status in availability.items()
        ]
        await asyncio.gather(*tasks)  # ✅ БД-запросы идут параллельно

    return availability

async def check_username_via_fragment(session, username: str) -> str:
    """Проверка статуса через Fragment. Анализирует редирект и 'Unavailable'."""

    # 🔥 Добавляем инициализацию SSL-контекста прямо в функцию
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    url_username = f"https://fragment.com/username/{username}"
    url_query = f"https://fragment.com/?query={username}"

    logging.info(f"[CHECK] 🔎 Проверяем final=query. if true > свободно @{username}")

    try:
        async with session.get(url_username, ssl=ssl_context, allow_redirects=True) as response:
            final_url = str(response.url)

            if final_url == url_query:
                logging.info(f"[RESULT]🔹 @{username} свободно.")
                return "Свободно"

            html = await response.text()
            return await analyze_username_page(html, username)

    except Exception as e:
        print(f"[ERROR] ❗ Ошибка запроса @{username}: {e}")
        return "Невозможно определить"


async def analyze_username_page(html: str, username: str) -> str:
    """Анализирует страницу конкретного username на Fragment."""
    soup = BeautifulSoup(html, 'html.parser')

    status_element = soup.find("span", class_="tm-section-header-status")
    if status_element:
        status_text = status_element.text.strip().lower()

        if "available" in status_text:
            logging.info(f"[RESULT] ⚠️ @{username} доступен для покупки.")
            return "Доступно для покупки"
        elif "sold" in status_text:
            logging.info(f"[RESULT] ❌ @{username} продан.")
            return "Продано"
        elif "taken" in status_text:
            logging.info(f"[RESULT] ❌ @{username} уже занят.")
            return "Занято"

    logging.info(f"[WARNING] ⚠️ Статус @{username} не определён.")
    return "Невозможно определить"



### ✅ 3. ПРОВЕРКА КОРРЕКТНОСТИ ВВЕДЕННОГО USERNAME
def is_valid_username(username: str) -> bool:
    pattern = r"^(?!.*__)[a-zA-Z0-9](?:[a-zA-Z0-9_]{3,30})[a-zA-Z0-9]$"
    return bool(re.match(pattern, username))


