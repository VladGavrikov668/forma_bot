from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from bot.models.user import User
from bot.utils.db import get_session
from sqlalchemy.future import select
from bot.keyboards.reply import get_admin_keyboard


class BlockUserState(StatesGroup):
    waiting_for_user_id = State()


class UnblockUserState(StatesGroup):
    waiting_for_user_id = State()


async def cmd_admin(message: types.Message):
    async with get_session() as session:
        user = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
        user = user.scalar_one_or_none()

        if user and user.is_admin:
            await message.reply("Панель администратора:", reply_markup=get_admin_keyboard())
        else:
            await message.reply("У вас нет доступа к этой команде.")


async def cmd_list_users(message: types.Message):
    async with get_session() as session:
        users = await session.execute(select(User))
        users = users.scalars().all()

        user_list = "\n".join(
            [f"ID: {user.id}, Username: {user.username}, Admin: {user.is_admin}, Blocked: {user.is_blocked}" for user in
             users])
        await message.reply(f"Список пользователей:\n{user_list}")


async def cmd_block_user(message: types.Message):
    await BlockUserState.waiting_for_user_id.set()
    await message.reply("Введите ID пользователя, которого хотите заблокировать:")


async def process_block_user(message: types.Message, state: FSMContext):
    user_id = int(message.text)
    async with get_session() as session:
        user = await session.get(User, user_id)
        if user:
            user.is_blocked = True
            await session.commit()
            await message.reply(f"Пользователь с ID {user_id} успешно заблокирован.")
        else:
            await message.reply("Пользователь не найден.")
    await state.finish()


async def cmd_unblock_user(message: types.Message):
    await UnblockUserState.waiting_for_user_id.set()
    await message.reply("Введите ID пользователя, которого хотите разблокировать:")


async def process_unblock_user(message: types.Message, state: FSMContext):
    user_id = int(message.text)
    async with get_session() as session:
        user = await session.get(User, user_id)
        if user:
            user.is_blocked = False
            await session.commit()
            await message.reply(f"Пользователь с ID {user_id} успешно разблокирован.")
        else:
            await message.reply("Пользователь не найден.")
    await state.finish()


def register_admin_handlers(dp: Dispatcher):
    dp.register_message_handler(cmd_admin, commands=["admin"])
    dp.register_message_handler(cmd_list_users, commands=["list_users"])
    dp.register_message_handler(cmd_list_users, text="Список пользователей")
    dp.register_message_handler(cmd_block_user, commands=["block_user"])
    dp.register_message_handler(cmd_block_user, text="Заблокировать пользователя")
    dp.register_message_handler(process_block_user, state=BlockUserState.waiting_for_user_id)
    dp.register_message_handler(cmd_unblock_user, commands=["unblock_user"])
    dp.register_message_handler(cmd_unblock_user, text="Разблокировать пользователя")
    dp.register_message_handler(process_unblock_user, state=UnblockUserState.waiting_for_user_id)