from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from bot.models.user import User, Block, Task
from bot.utils.db import get_session
from sqlalchemy.future import select
from bot.keyboards.reply import get_main_keyboard
from bot.keyboards.inline import get_block_keyboard, get_task_keyboard


class CreateBlockState(StatesGroup):
    waiting_for_name = State()


class CreateTaskState(StatesGroup):
    waiting_for_title = State()
    waiting_for_description = State()


async def cmd_start(message: types.Message):
    async with get_session() as session:
        user = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
        user = user.scalar_one_or_none()

        if not user:
            new_user = User(telegram_id=message.from_user.id, username=message.from_user.username)
            session.add(new_user)
            await session.commit()
            await message.reply("Добро пожаловать! Вы успешно зарегистрированы.", reply_markup=get_main_keyboard())
        else:
            await message.reply("С возвращением!", reply_markup=get_main_keyboard())


async def cmd_create_block(message: types.Message):
    await CreateBlockState.waiting_for_name.set()
    await message.reply("Введите название нового блока:")


async def process_block_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['block_name'] = message.text

    async with get_session() as session:
        user = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
        user = user.scalar_one_or_none()

        if user:
            new_block = Block(name=data['block_name'], creator_id=user.id)
            session.add(new_block)
            await session.commit()
            await message.reply(f"Блок '{data['block_name']}' успешно создан!", reply_markup=get_main_keyboard())
        else:
            await message.reply("Произошла ошибка. Пожалуйста, попробуйте снова.")

    await state.finish()


async def cmd_my_blocks(message: types.Message):
    async with get_session() as session:
        user = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
        user = user.scalar_one_or_none()

        if user:
            blocks = await session.execute(select(Block).where(Block.creator_id == user.id))
            blocks = blocks.scalars().all()

            if blocks:
                for block in blocks:
                    await message.reply(f"Блок: {block.name}", reply_markup=get_block_keyboard(block.id))
            else:
                await message.reply("У вас пока нет созданных блоков.")
        else:
            await message.reply("Произошла ошибка. Пожалуйста, попробуйте снова.")


async def process_callback(callback_query: types.CallbackQuery, state: FSMContext):
    action, id_str = callback_query.data.split(':')
    id = int(id_str)

    if action == 'add_task':
        await CreateTaskState.waiting_for_title.set()
        await state.update_data(block_id=id)
        await callback_query.message.reply("Введите название задачи:")
    elif action == 'view_tasks':
        await view_tasks(callback_query.message, id)
    elif action == 'delete_block':
        await delete_block(callback_query.message, id)
    elif action == 'edit_task':
        # Implement task editing
        pass
    elif action == 'delete_task':
        await delete_task(callback_query.message, id)

    await callback_query.answer()







async def delete_block(message: types.Message, block_id: int):
    async with get_session() as session:
        block = await session.get(Block, block_id)
        if block:
            await session.delete(block)
            await session.commit()
            await message.reply("Блок успешно удален.", reply_markup=get_main_keyboard())
        else:
            await message.reply("Блок не найден.")


async def delete_task(message: types.Message, task_id: int):
    async with get_session() as session:
        task = await session.get(Task, task_id)
        if task:
            await session.delete(task)
            await session.commit()
            await message.reply("Задача успешно удалена.")
        else:
            await message.reply("Задача не найдена.")


def register_user_handlers(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands=["start"])
    dp.register_message_handler(cmd_create_block, commands=["create_block"])
    dp.register_message_handler(cmd_create_block, text="Создать блок")
    dp.register_message_handler(process_block_name, state=CreateBlockState.waiting_for_name)
    dp.register_message_handler(cmd_my_blocks, commands=["my_blocks"])
    dp.register_message_handler(cmd_my_blocks, text="Мои блоки")
    dp.register_callback_query_handler(process_callback)
    dp.register_message_handler(process_task_title, state=CreateTaskState.waiting_for_title)
    dp.register_message_handler(process_task_description, state=CreateTaskState.waiting_for_description)