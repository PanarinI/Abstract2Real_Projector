# Цель: Протестировать 4 последовательных взаимодействия с AI, передавая контекст и выбор пользователя на каждом шаге.
# Формат взаимодействия: Скрипт запрашивает у AI варианты, «выбирает» один из них случайным образом или по заданному сценарию, и передаёт выбор в следующий запрос.
import os
import random
from dotenv import load_dotenv
from openai import OpenAI

from bot import config
import logging

logging.basicConfig(level=logging.INFO)


# Загрузка переменных окружения
load_dotenv()

# Получение ключей API из окружения
API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL")


# Создание клиента OpenAI для генерации username
client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

# Функция для отправки запроса к AI
def ask_ai(prompt: str) -> str:
    try:
        response = client.chat.completions.create(
            model_name=config.model_name,
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

# Изначальные данные
username = "TherapyThoughts"


# парсер ответа от AI
def parse_ai_response(response: str) -> dict:
    parsed_data = {
        "answer": "",  # Совмещённый комментарий и вопрос
        "options": []
    }

    lines = response.strip().split('\n')
    for line in lines:
        line = line.strip()
        if not line:  # Пропускаем пустые строки
            continue
        if line.lower().startswith("ответ ai:"):
            parsed_data["answer"] = line.split(":", 1)[1].strip()
        elif line[0].isdigit() and '.' in line:
            parsed_data["options"].append(line.split('.', 1)[1].strip())

    return parsed_data


# Первый этап: ЧТО
def first_stage():
    global first_choice
    prompt = f"""
    Пользователь выбрал username "{username}".
    Он еще не знает, что он хочет сделать на основе этого имени.
    Проанализируй "{username}" с точки зрения смысла, ассоциаций и контекстов.
    ДПредложи 3 чётких варианта того, в каком формате может реализоваться бренд.
    Ответ дай в формате списка, пиши кратко - не больше 2-15 слов на вариант:
    [Краткий комментарий к выбору {username} и подводка к вопросу (1 предложение),
    1. Вариант один
    2. Вариант два
    3. Вариант три
    """

    response = ask_ai(prompt)
    print("Этап ФОРМАТ:")
    print(response)

    parsed_response = parse_ai_response(response)
    print(f"Ответ AI: {parsed_response['answer']}")
    print(f"Варианты: {parsed_response['options']}")

    if parsed_response["options"]:
        first_choice = random.choice(parsed_response["options"])
        print(f"Выбор пользователя: {first_choice}\n")
    else:
        print("Нет доступных вариантов выбора на этапе ЧТО.")


# Второй этап: КАКОЕ
def second_stage():
    global second_choice
    prompt = f"""
    Пользователь выбрал имя "{username}".
    Пользователь выбрал формат "{first_choice}"
    Предложи 3 варианта того, в каком направлении 
    может развиваться проект "{username}". Кто будет этим пользоваться?
    Ответ дай в формате списка, пиши кратко - не больше 12-15 слов на вариант:
    [Краткий комментарий к выбору {first_choice} и подводка к вопросу (1 предложение),
    1. Вариант один
    2. Вариант два
    3. Вариант три]
    """

    response = ask_ai(prompt)
    print("Этап АУДИТОРИЯ:")
    print(response)

    parsed_response = parse_ai_response(response)
    print(f"Ответ AI: {parsed_response['answer']}")
    print(f"Варианты: {parsed_response['options']}")

    if parsed_response["options"]:
        second_choice = random.choice(parsed_response["options"])
        print(f"Выбор пользователя: {second_choice}\n")
    else:
        print("Нет доступных вариантов выбора на этапе КАКОЕ.")


# Третий этап: ЗАЧЕМ
def third_stage():
    global third_choice
    prompt = f"""
    Ты - креативный генератор идей и концепций (телеграм-бот). Мы разрабатываем концепт уникального проекта на основе выбранного телеграм-username.
    В формате диалога. Ты комментируешь выбор и предлагаешь идеи.
    Пользователь выбрал имя "{username}".
    Пользователь выбрал формат "{first_choice}" и его направление "{second_choice}".
    На основании семантики, ассоциаций username, выбранного формата и направления 
    предложи 3 варианты сути и ценности проекта - что это такое?
    Ответ дай в формате списка, пиши кратко - не больше 12-15 слов на вариант:

    [Краткий комментарий к выбору {second_choice} и подводка к вопросу (1 предложение),
    1. Вариант один
    2. Вариант два
    3. Вариант три]
    """

    response = ask_ai(prompt)
    print("Этап СУТЬ:")
    print(response)

    parsed_response = parse_ai_response(response)
    print(f"Ответ AI: {parsed_response['answer']}")
    print(f"Варианты: {parsed_response['options']}")

    if parsed_response["options"]:
        third_choice = random.choice(parsed_response["options"])
        print(f"Выбор пользователя: {third_choice}\n")
    else:
        print("Нет доступных вариантов выбора на этапе ЗАЧЕМ.")


# Четвёртый этап: Финальный профиль
def final_stage():
    print("Финальный профиль проекта:")
    print(f"Username: {username}")
    print(f"Формат проекта: {first_choice}")
    print(f"Характер проекта: {second_choice}")
    print(f"Суть и ценность: {third_choice}\n")

    # Новый запрос к AI: добавление полезной информации
    prompt = f"""
    Пользователь выбрал:
    - Username: "{username}"
    - Формат: "{first_choice}"
    - Характер: "{second_choice}"
    - Суть и ценность: "{third_choice}"

    Добавь к профилю проекта полезные рекомендации:
    1. Идеи для контент-стратегии (1-2 идеи).
    2. Советы по продвижению проекта в соцсетях.
    3. Основание визуального стиля (кратко).

    Ответ дай лаконично, не более 40 слов.
    """

    response = ask_ai(prompt)
    print("Дополнительные рекомендации:")
    print(response)



# Последовательное выполнение всех этапов
def run_test():
    first_stage()
    second_stage()
    third_stage()
    final_stage()


# Запуск теста
if __name__ == "__main__":
    run_test()