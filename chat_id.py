@brand_router.message()
async def get_chat_id(message: types.Message):
    """
    Получает ID группы, куда отправлено сообщение.
    """
    chat_id = message.chat.id
    await message.answer(f"ID этой группы: <code>{chat_id}</code>", parse_mode="HTML")
