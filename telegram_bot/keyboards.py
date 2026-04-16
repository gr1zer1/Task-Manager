from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Мои задачи"), KeyboardButton(text="📝 Назначенные")],
            [KeyboardButton(text="➕ Новая задача"), KeyboardButton(text="✅ Отметить выполненной")],
            [KeyboardButton(text="❓ Помощь")]
        ],
        resize_keyboard=True
    )
