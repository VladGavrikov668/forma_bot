from typing import Union, List

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, \
    ReplyKeyboardRemove
from emoji import emojize

from entities.user import User
from settings import app_settings


def btn_back(previous_menu: str) -> InlineKeyboardButton:
    """Button for returning to previous menu in UI."""
    return InlineKeyboardButton(text='Назад', callback_data=previous_menu)


def btn_prev_page(page: int, cb_name: str, cb_arg: str = None) -> Union[InlineKeyboardButton, None]:
    """Создаёт инлайн-кнопку с текстом "Назад" для возврата в предыдущее меню."""
    if page > 1:
        page -= 1
        if cb_arg is None:
            return InlineKeyboardButton(text=f'{emojize(":left_arrow:")}', callback_data=f'{cb_name}:{page}')
        else:
            return InlineKeyboardButton(text=f'{emojize(":left_arrow:")}', callback_data=f'{cb_name}:{cb_arg}:{page}')
    else:
        return InlineKeyboardButton(text='', callback_data=':')


def btn_next_page(max_page: int, page: int, cb_name: str, cb_arg: str = None) -> InlineKeyboardButton:
    """Создаёт инлайн-кнопку для перехода на предыдущую страницу в пагинированных данных."""
    if page < max_page:
        page += 1
        if cb_arg is None:
            return InlineKeyboardButton(text=f'{emojize(":right_arrow:")}', callback_data=f'{cb_name}:{page}')
        else:
            return InlineKeyboardButton(text=f'{emojize(":right_arrow:")}', callback_data=f'{cb_name}:{cb_arg}:{page}')
    else:
        return InlineKeyboardButton(text='', callback_data=':')


def main_menu(is_admin: bool) -> ReplyKeyboardMarkup:
    if is_admin:
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.row(
            KeyboardButton(text='Админ панель'),
            KeyboardButton(text='Отчет'),
        )
    else:
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.row(
            KeyboardButton(text='Отчет')
        )
    return kb


def admin_panel() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton(text='Пользователи', callback_data='users:1')
    )
    kb.row(
        InlineKeyboardButton(text='Ключи', callback_data='keys')
    )
    return kb


def keys() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton(text='Сгенерировать ключи', callback_data='generate_keys')
    )
    kb.row(
        InlineKeyboardButton(text='Посмотреть ключи', callback_data='show_keys')
    )
    kb.row(
        InlineKeyboardButton(text='Назад', callback_data='admin_panel')
    )
    return kb


def users(
        user_list: List[User],
        max_page: int,
        page: int,
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=app_settings.PAGINATION_LIMIT + 2)  # По кнопке на лимит + стрелки пагинации
    user_buttons = []
    for i, user in enumerate(user_list):
        user_buttons.append(
            InlineKeyboardButton(
                text=f'{(1 + app_settings.PAGINATION_LIMIT * (page - 1)) + i}',
                callback_data=f'user:{user.telegram_id}:{page}',
            )
        )
    kb.row(
        btn_prev_page(page, 'users'),
        *user_buttons,
        btn_next_page(max_page, page, 'users'),
    )
    kb.row(
        btn_back('admin_panel'),
    )
    return kb


def user(user_model: User, page: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    if user_model.is_admin:
        kb.row(
            InlineKeyboardButton(text='Убрать админа', callback_data=f'unmake_admin:{user_model.telegram_id}:{page}')
        )
    else:
        kb.row(
            InlineKeyboardButton(text='Сделать админом', callback_data=f'make_admin:{user_model.telegram_id}:{page}')
        )
    kb.row(
        InlineKeyboardButton(text='Удалить', callback_data=f'delete:{user_model.telegram_id}:{page}')
    )
    kb.row(
        InlineKeyboardButton(text='Назад', callback_data=f'users:{page}')
    )
    return kb


def confirm_delete_user(user_model: User, page: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton(text='Да, удалить', callback_data=f'confirm_delete:{user_model.telegram_id}:{page}')
    )
    kb.row(
        InlineKeyboardButton(text='Нет, вернуться', callback_data=f'user:{user_model.telegram_id}:{page}')
    )
    return kb