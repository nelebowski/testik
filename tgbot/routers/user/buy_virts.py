# - *- coding: utf-8 - *-
"""Flow for buying virtual currency."""
from aiogram import Router, F, Bot
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, Message

from tgbot.keyboards.inline_buy import servers_kb, payment_methods_kb, SERVERS
from tgbot.utils.misc.bot_models import FSM

router = Router(name=__name__)


def parse_amount(text: str) -> int:
    text = text.lower().replace(' ', '')
    if 'кк' in text or 'kk' in text:
        num = text.replace('кк', '').replace('kk', '').replace(',', '.')
        return int(float(num) * 1_000_000)
    digits = ''.join(ch for ch in text if ch.isdigit())
    return int(digits)


@router.callback_query(F.data == 'buy_start')
async def buy_start(call: CallbackQuery, state: FSM):
    await state.set_state('buy_server')
    await call.message.edit_text('<b>Выберите сервер:</b>', reply_markup=servers_kb(0))


@router.callback_query(F.data.startswith('servers_page:'), StateFilter('buy_server'))
async def servers_page(call: CallbackQuery, state: FSM):
    page = int(call.data.split(':')[1])
    await call.message.edit_reply_markup(reply_markup=servers_kb(page))


@router.callback_query(F.data.startswith('server_select:'), StateFilter('buy_server'))
async def server_selected(call: CallbackQuery, state: FSM):
    idx = int(call.data.split(':')[1])
    server = SERVERS[idx]
    await state.update_data(server=server)
    await state.set_state('buy_amount')
    await call.message.edit_text(
        f'<b>Сервер {server}</b>\nВведите количество валюты (например 1кк):'
    )


@router.message(StateFilter('buy_amount'))
async def amount_input(message: Message, state: FSM):
    amount = parse_amount(message.text)
    price = amount / 1_000_000 * 99
    await state.update_data(amount=amount, price=price)
    await state.set_state('buy_account')
    await message.answer('Введите ваш банковский счет:')


@router.message(StateFilter('buy_account'))
async def account_input(message: Message, state: FSM):
    account = message.text
    data = await state.get_data()
    server = data['server']
    amount = data['amount']
    price = data['price']
    await state.update_data(account=account)
    await state.set_state('buy_payment')
    await message.answer(
        f'<b>Проверка заказа</b>\n'
        f'Сервер: <code>{server}</code>\n'
        f'Количество: <code>{amount}</code>\n'
        f'Цена: <code>{price:.2f} ₽</code>\n'
        f'Счет: <code>{account}</code>\n'
        f'Выберите способ оплаты:',
        reply_markup=payment_methods_kb()
    )


@router.callback_query(F.data.startswith('pay_method:'), StateFilter('buy_payment'))
async def payment_choose(call: CallbackQuery, state: FSM, bot: Bot):
    method = call.data.split(':')[1]
    data = await state.get_data()
    price = data['price']
    if method == 'stars':
        stars = int((price / 1.4) + 0.999)
        await call.message.answer(f'Отправьте боту {stars}⭐️ (звезд).')
    elif method == 'cryptobot':
        await call.message.answer(f'Оплатите {price:.2f} ₽ через CryptoBot.')
    else:
        await call.message.answer(f'Оплатите {price:.2f} ₽ через YooMoney.')
    await call.message.answer('Ура! Ваш заказ принят, ожидайте вирты в течении 10 минут.')
    await state.clear()
