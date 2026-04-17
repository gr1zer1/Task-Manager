from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def get_guest_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔐 Войти"), KeyboardButton(text="🆕 Регистрация")],
            [KeyboardButton(text="❓ Помощь")],
        ],
        resize_keyboard=True,
    )


def get_main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Мои задачи"), KeyboardButton(text="📝 Назначенные")],
            [KeyboardButton(text="➕ Новая задача"), KeyboardButton(text="✅ Отметить выполненной")],
            [KeyboardButton(text="🚪 Выйти"), KeyboardButton(text="❓ Помощь")],
        ],
        resize_keyboard=True,
    )
