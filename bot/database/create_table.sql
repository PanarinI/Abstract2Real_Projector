CREATE TABLE IF NOT EXISTS generated_usernames (
    id SERIAL PRIMARY KEY,
    username VARCHAR(32) UNIQUE NOT NULL, --уникальный username 32 символа максимум
    status TEXT NOT NULL,
    category TEXT, -- категория (например, бизнес, технологии).
    context TEXT NOT NULL, -- исходный запрос пользователя.
    style TEXT DEFAULT NULL, -- добавляем новый столбец style (по умолчанию NULL)
    llm TEXT NOT NULL, -- используемая LLM
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- время генерации.
);
