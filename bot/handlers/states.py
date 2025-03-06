from aiogram.fsm.state import State, StatesGroup

class BrandCreationStates(StatesGroup):
    waiting_for_context = State()          # Ввод мысли пользователя
    waiting_for_style = State()            # Ожидание выбора стиля
    waiting_for_username_choice = State()  # Выбор username
    waiting_for_stage1 = State()           # Этап выбора формата проекта
    waiting_for_stage2 = State()         # Этап выбора аудитории
    waiting_for_stage3 = State()            # Этап определения сути проекта
    project_ready = State()               # 🔥
    waiting_for_custom_input = State()  # Новое состояние для ввода своего варианта
    waiting_for_rating = State() # ожидание оценки
    waiting_for_feedback = State()  # Состояние комментария

