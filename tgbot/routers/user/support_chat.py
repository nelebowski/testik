# - *- coding: utf-8 - *-
"""Simple support chat between user and admins."""
from aiogram import Router, F, Bot
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from tgbot.data.config import get_admins
from tgbot.keyboards.inline_main_menu import start_menu_finl
from tgbot.utils.const_functions import ikb
from tgbot.utils.misc.bot_models import FSM

router = Router(name=__name__)


@router.callback_query(F.data == 'support_start')
async def support_start(call: CallbackQuery, state: FSM):
    await state.set_state('support_chat')
    await call.message.edit_text('Напишите сообщение для поддержки. Для выхода используйте /stop.')


@router.message(StateFilter('support_chat'))
async def support_message(message: Message, state: FSM, bot: Bot):
    for admin in get_admins():
        await bot.send_message(admin, f'Сообщение от {message.from_user.id}:\n{message.text}')
    await message.answer('Сообщение отправлено. Ожидайте ответа администратора.')


@router.message(F.text.startswith('/reply'))
async def admin_reply(message: Message, bot: Bot):
    if message.from_user.id not in get_admins():
        return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer('Использование: /reply <user_id> <текст>')
        return
    user_id = int(parts[1])
    text = parts[2]
    await bot.send_message(user_id, f'Ответ поддержки:\n{text}')
    await message.answer('Отправлено.')


@router.message(F.text == '/stop', StateFilter('support_chat'))
async def support_stop(message: Message, state: FSM):
    await state.clear()
    await message.answer('Диалог с поддержкой завершен.', reply_markup=start_menu_finl())


@router.callback_query(F.data == 'reviews_start')
async def reviews_start(call: CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.row(ikb('🔙 В меню', data='back_to_menu'))
    await call.message.edit_text('Отзывы пока отсутствуют.', reply_markup=kb.as_markup())
