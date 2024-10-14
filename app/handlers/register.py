from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from app.db.postgres.models import User, Role, Block, Token, RoleName
from app.db.postgres.database import get_db
from aiogram.dispatcher.filters.state import State, StatesGroup

# Определение состояний для регистрации
class RegistrationStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_position = State()
    waiting_for_block = State()
    waiting_for_token = State()

# Обработчики
async def cmd_start(message: types.Message):
    async for db in get_db():  # Используем async for для асинхронного генератора
        result = await db.execute(select(User).filter(User.telegram_id == message.from_user.id))
        user = result.scalars().first()  # Получаем пользователя

        if user:
            await message.reply(f"Добро пожаловать, {user.username}!")
        else:
            await message.reply("Добро пожаловать! Давайте начнем регистрацию.")
            await RegistrationStates.waiting_for_name.set()
            await message.reply("Пожалуйста, введите ваши ФИО в формате 'Иванов Иван Иванович':")

async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(full_name=message.text.strip())
    await RegistrationStates.waiting_for_position.set()
    await message.reply("Спасибо. Теперь введите вашу должность:")

async def process_position(message: types.Message, state: FSMContext):
    await state.update_data(position=message.text.strip())
    await RegistrationStates.waiting_for_block.set()

    async for db in get_db():
        result = await db.execute(select(Block))
        blocks = result.scalars().all()  # Получаем все блоки

        if not blocks:
            await message.reply("В базе данных нет доступных блоков. Пожалуйста, обратитесь к администратору.")
            await state.finish()
            return

        keyboard = types.InlineKeyboardMarkup()
        for block in blocks:
            keyboard.add(types.InlineKeyboardButton(block.name, callback_data=f"block_{block.id}"))

        await message.reply("Выберите ваш блок:", reply_markup=keyboard)

async def process_block_selection(callback_query: types.CallbackQuery, state: FSMContext):
    block_id = int(callback_query.data.split('_')[1])
    await state.update_data(block_id=block_id)
    await callback_query.answer()
    await callback_query.message.answer("Спасибо за выбор блока. Теперь, пожалуйста, введите токен для регистрации.")
    await RegistrationStates.waiting_for_token.set()


async def process_token(message: types.Message, state: FSMContext):
    token_value = message.text.strip()
    async for db in get_db():
        async with db.begin():
            result = await db.execute(select(Token).filter(Token.value == token_value))
            token = result.scalars().first()  # Получаем токен

            if not token:
                await message.reply("Неверный токен. Пожалуйста, попробуйте снова или обратитесь к администратору.")
                await RegistrationStates.waiting_for_token.set()
                return

            user_data = await state.get_data()

            try:
                role_result = await db.execute(select(Role).filter(Role.name == RoleName.USER))
                user_role = role_result.scalars().first()

                new_user = User(
                    telegram_id=message.from_user.id,
                    role_id=user_role.id if user_role else None,
                    block_id=user_data['block_id'],
                    username=message.from_user.username or user_data['full_name'],
                    full_name=user_data['full_name'],
                    is_block_manager=False,
                    is_admin=False,
                )
                db.add(new_user)

                # Удаляем токен
                await db.delete(token)

                # Коммит происходит автоматически при выходе из контекстного менеджера

                await message.reply("Регистрация успешно завершена!")
            except IntegrityError:
                # Откат происходит автоматически при возникновении исключения
                await message.reply("Произошла ошибка при регистрации. Возможно, вы уже зарегистрированы.")
            finally:
                await state.finish()

async def token_input(message: types.Message):
    await message.reply("Пожалуйста, введите токен для регистрации:")

# Регистрация хендлеров
def register_all_handlers(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands=['start'])
    dp.register_message_handler(process_name, state=RegistrationStates.waiting_for_name)
    dp.register_message_handler(process_position, state=RegistrationStates.waiting_for_position)
    dp.register_callback_query_handler(process_block_selection, lambda c: c.data and c.data.startswith('block_'),
                                       state=RegistrationStates.waiting_for_block)
    dp.register_message_handler(process_token, state=RegistrationStates.waiting_for_token)
    dp.register_message_handler(token_input, state=RegistrationStates.waiting_for_token)
