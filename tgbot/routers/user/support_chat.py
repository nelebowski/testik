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
    kb = InlineKeyboardBuilder()
    kb.row(ikb('❌ Завершить', data='support_stop'))
    kb.row(ikb('🔙 В меню', data='back_to_menu'))
    await call.message.edit_text(
        'Опишите вашу проблему, администратор свяжется с вами здесь.',
        reply_markup=kb.as_markup(),
    )


@router.message(StateFilter('support_chat'))
async def support_message(message: Message, state: FSM, bot: Bot):
    """Send user message to admins with reply and close buttons."""
    admin_kb = InlineKeyboardBuilder()
    admin_kb.row(ikb('Ответить', data=f'support_reply:{message.from_user.id}'))
    admin_kb.row(ikb('Завершить', data=f'support_close:{message.from_user.id}'))
    for admin in get_admins():
        await bot.send_message(
            admin,
            f'Пользователь {message.from_user.id} написал:\n{message.text}',
            reply_markup=admin_kb.as_markup(),
        )
    user_kb = InlineKeyboardBuilder()
    user_kb.row(ikb('❌ Завершить', data='support_stop'))
    user_kb.row(ikb('🔙 В меню', data='back_to_menu'))
    await message.answer(
        'Сообщение отправлено. Ожидайте ответа администратора.',
        reply_markup=user_kb.as_markup(),
    )


@router.callback_query(F.data.startswith('support_reply:'), F.from_user.id.in_(get_admins()))
async def support_reply_call(call: CallbackQuery, state: FSM):
    user_id = int(call.data.split(':')[1])
    await state.update_data(reply_to=user_id)
    await state.set_state('support_admin_reply')
    kb = InlineKeyboardBuilder()
    kb.row(ikb('❌ Отмена', data='support_cancel'))
    await call.message.answer(f'Введите ответ для пользователя {user_id}.', reply_markup=kb.as_markup())
    await call.answer()


@router.message(StateFilter('support_admin_reply'), F.from_user.id.in_(get_admins()))
async def support_admin_reply(message: Message, state: FSM, bot: Bot):
    data = await state.get_data()
    user_id = data['reply_to']
    user_kb = InlineKeyboardBuilder()
    user_kb.row(ikb('❌ Завершить', data='support_stop'))
    user_kb.row(ikb('🔙 В меню', data='back_to_menu'))
    await bot.send_message(
        user_id,
        f'Ответ поддержки:\n{message.text}',
        reply_markup=user_kb.as_markup(),
    )
    await message.answer('Отправлено.')
    await state.clear()


@router.callback_query(F.data == 'support_cancel', StateFilter('support_admin_reply'), F.from_user.id.in_(get_admins()))
async def support_admin_cancel(call: CallbackQuery, state: FSM):
    await state.clear()
    await call.message.edit_text('Отменено.')
    await call.answer()


@router.callback_query(F.data == 'support_stop', StateFilter('support_chat'))
@router.message(F.text == '/stop', StateFilter('support_chat'))
async def support_stop(event, state: FSM):
    await state.clear()
    if isinstance(event, CallbackQuery):
        await event.message.edit_text('Диалог с поддержкой завершен.', reply_markup=start_menu_finl())
        await event.answer()
    else:
        await event.answer('Диалог с поддержкой завершен.', reply_markup=start_menu_finl())


@router.callback_query(F.data.startswith('support_close:'), F.from_user.id.in_(get_admins()))
async def support_close(call: CallbackQuery, bot: Bot):
    user_id = int(call.data.split(':')[1])
    await bot.send_message(user_id, 'Диалог с поддержкой завершен.', reply_markup=start_menu_finl())
    await call.message.answer('Диалог закрыт.')
    await call.answer()


@router.callback_query(F.data == 'reviews_start')
async def reviews_start(call: CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.row(ikb('🔙 В меню', data='back_to_menu'))
    await call.message.edit_text('Отзывы пока отсутствуют.', reply_markup=kb.as_markup())
