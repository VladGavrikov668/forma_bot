import asyncio
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from app.config import API_TOKEN
from app.handlers import register_all_handlers

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


async def main():
    # Регистрация всех обработчиков
    register_all_handlers(dp)

    # Запуск бота
    try:
        await dp.start_polling()
    finally:
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(main())
