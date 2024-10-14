import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError


from app.db.postgres.models import User, Role, Block, Token, RoleName
from app.db.postgres.database import get_db, engine
from app.main import dp, bot


# Определение состояний для регистрации
class RegistrationStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_position = State()
    waiting_for_block = State()
    waiting_for_token = State()


# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    db = next(get_db())
    user = db.query(User).filter(User.telegram_id == message.from_user.id).first()
    if user:
        await message.reply(f"Добро пожаловать, {user.username}!")
    else:
        await message.reply("Добро пожаловать! Давайте начнем регистрацию.")
        await RegistrationStates.waiting_for_name.set()
        await message.reply("Пожалуйста, введите ваши ФИО:")


# Обработчик ввода ФИО
@dp.message_handler(state=RegistrationStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(full_name=message.text.strip())
    await RegistrationStates.waiting_for_position.set()
    await message.reply("Спасибо. Теперь введите вашу должность:")


# Обработчик ввода должности
@dp.message_handler(state=RegistrationStates.waiting_for_position)
async def process_position(message: types.Message, state: FSMContext):
    await state.update_data(position=message.text.strip())
    await RegistrationStates.waiting_for_block.set()

    db = next(get_db())
    blocks = db.query(Block).all()

    if not blocks:
        await message.reply("В базе данных нет доступных блоков. Пожалуйста, обратитесь к администратору.")
        await state.finish()
        return

    keyboard = types.InlineKeyboardMarkup()
    for block in blocks:
        keyboard.add(types.InlineKeyboardButton(block.name, callback_data=f"block_{block.id}"))

    await message.reply("Выберите ваш блок:", reply_markup=keyboard)


# Обработчик выбора блока
@dp.callback_query_handler(lambda c: c.data and c.data.startswith('block_'), state=RegistrationStates.waiting_for_block)
async def process_block_selection(callback_query: types.CallbackQuery, state: FSMContext):
    block_id = int(callback_query.data.split('_')[1])
    await state.update_data(block_id=block_id)
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id,
                           "Спасибо за выбор блока. Теперь, пожалуйста, введите токен для регистрации.")
    await RegistrationStates.waiting_for_token.set()


# Обработчик ввода токена
@dp.message_handler(state=RegistrationStates.waiting_for_token)
async def process_token(message: types.Message, state: FSMContext):
    token_value = message.text.strip()
    db = next(get_db())
    token = db.query(Token).filter(Token.value == token_value).first()

    if not token:
        await message.reply("Неверный токен. Пожалуйста, попробуйте снова или обратитесь к администратору.")
        return

    user_data = await state.get_data()

    try:
        # Создание нового пользователя
        new_user = User(
            telegram_id=message.from_user.id,
            username=user_data['full_name'],
            role_id=db.query(Role).filter(Role.name == RoleName.USER).first().id
        )
        db.add(new_user)
        db.flush()  # Чтобы получить id нового пользователя

        # Удаление использованного токена
        db.delete(token)
        db.commit()

        await message.reply("Регистрация успешно завершена!")
    except IntegrityError:
        db.rollback()
        await message.reply("Произошла ошибка при регистрации. Возможно, вы уже зарегистрированы.")
    finally:
        await state.finish()
