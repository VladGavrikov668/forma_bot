from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("Мои блоки"))
    keyboard.add(KeyboardButton("Создать блок"))
    return keyboard

