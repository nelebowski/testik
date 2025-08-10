# -*- coding: utf-8 -*-
"""Flow for buying virtual currency with multiple payment methods."""
from math import ceil

from aiogram import Router, F, Bot
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, Message, LabeledPrice

from tgbot.data.config import get_admins
from tgbot.keyboards.inline_buy import (
    SERVERS,
    payment_methods_kb,
    payment_bill_kb,
    servers_kb,
)
from tgbot.services.api_cryptobot import CryptobotAPI
from tgbot.services.api_yoomoney import YoomoneyAPI
from tgbot.utils.misc.bot_models import FSM, ARS

router = Router(name=__name__)


def parse_amount(text: str) -> int:
    """Парсит суммы вида: 1.5кк, 500к, 1500000."""
    t = text.lower().replace(" ", "")
    if "кк" in t or "kk" in t:
        num = t.replace("кк", "").replace("kk", "").replace(",", ".")
        return int(float(num) * 1_000_000)
    if "к" in t or "k" in t:
        num = t.replace("к", "").replace("k", "").replace(",", ".")
        return int(float(num) * 1_000)
    digits = "".join(ch for ch in t if ch.isdigit())
    return int(digits) if digits else 0


@router.callback_query(F.data == "buy_start")
async def buy_start(call: CallbackQuery, state: FSM):
    await state.set_state("buy_server")
    await call.message.edit_text("<b>Выберите сервер:</b>", reply_markup=servers_kb(0))
    await call.answer()


@router.callback_query(F.data.startswith("servers_page:"), StateFilter("buy_server"))
async def servers_page(call: CallbackQuery, state: FSM):
    page = int(call.data.split(":")[1])
    await call.message.edit_reply_markup(reply_markup=servers_kb(page))
    await call.answer()


@router.callback_query(F.data.startswith("server_select:"), StateFilter("buy_server"))
async def server_selected(call: CallbackQuery, state: FSM):
    idx = int(call.data.split(":")[1])
    server = SERVERS[idx]
    await state.update_data(server=server)
    await state.set_state("buy_amount")
    await call.message.edit_text(
        f"<b>Сервер {server}</b>\nВведите количество валюты (например 1кк):"
    )
    await call.answer()


@router.message(StateFilter("buy_amount"))
async def amount_input(message: Message, state: FSM):
    amount = parse_amount(message.text)
    if amount < 500_000:
        await message.answer("Минимальная сумма покупки — 0.5кк (500 000). Попробуйте снова:")
        return

    price = ceil(amount / 1_000_000 * 99)  # ₽
    await state.update_data(amount=amount, price=price)
    await state.set_state("buy_account")
    await message.answer("Введите ваш банковский счёт:")


@router.message(StateFilter("buy_account"))
async def account_input(message: Message, state: FSM):
    # простая валидация счёта
    if not message.text.isdigit() or len(message.text) > 7:
        await message.answer("Счёт должен содержать только цифры и быть не длиннее 7 знаков. Введите снова:")
        return

    account = message.text
    data = await state.get_data()
    server = data["server"]
    amount = data["amount"]
    price = data["price"]

    await state.update_data(account=account)
    await state.set_state("buy_payment")

    await message.answer(
        (
            f"<b>Проверка заказа</b>\n"
            f"Сервер: <code>{server}</code>\n"
            f"Количество: <code>{amount}</code>\n"
            f"Цена: <code>{price} ₽</code>\n"
            f"Счёт: <code>{account}</code>\n"
            f"Выберите способ оплаты:"
        ),
        reply_markup=payment_methods_kb(),
    )


@router.callback_query(F.data.startswith("pay_method:"), StateFilter("buy_payment"))
async def payment_choose(call: CallbackQuery, state: FSM, bot: Bot, arSession: ARS):
    """Сформировать счёт по выбранному способу оплаты."""
    method = call.data.split(":")[1]
    data = await state.get_data()
    price = data["price"]

    if method == "stars":
        # конвертируем рубли в звёзды (примерный курс)
        stars = ceil(price / 1.4)
        await bot.send_invoice(
            chat_id=call.from_user.id,
            title="Покупка виртов",
            description="Оплата заказа",
            payload="buy_virts",
            provider_token="",  # TODO: укажите реальный provider_token для Stars
            currency="XTR",
            prices=[LabeledPrice(label="Вирты", amount=stars)],
        )
        await call.message.answer("Оплатите счёт через Telegram Stars.")
        await state.update_data(pay_method="stars")
        await state.set_state("buy_wait_payment")
        await call.answer()
        return

    if method == "cryptobot":
        bill_message, bill_link, bill_receipt = await CryptobotAPI(
            bot=bot, arSession=arSession, update=call
        ).bill(price)
        if bill_message:
            await state.update_data(pay_method="cryptobot", bill_receipt=bill_receipt)
            await call.message.edit_text(
                bill_message,
                reply_markup=payment_bill_kb(bill_link, bill_receipt, "Cryptobot"),
            )
            await state.set_state("buy_wait_payment")
        else:
            await call.message.answer("Не удалось сгенерировать платёж. Попробуйте позже.")
        await call.answer()
        return

    # YooMoney по умолчанию
    bill_message, bill_link, bill_receipt = await YoomoneyAPI(
        bot=bot, arSession=arSession, update=call
    ).bill(price)
    if bill_message:
        await state.update_data(pay_method="yoomoney", bill_receipt=bill_receipt)
        await call.message.edit_text(
            bill_message,
            reply_markup=payment_bill_kb(bill_link, bill_receipt, "Yoomoney"),
        )
        await state.set_state("buy_wait_payment")
    else:
        await call.message.answer("Не удалось сгенерировать платёж. Попробуйте позже.")
    await call.answer()


@router.callback_query(F.data.startswith("BuyPay:Cryptobot"), StateFilter("buy_wait_payment"))
async def check_cryptobot(call: CallbackQuery, state: FSM, bot: Bot, arSession: ARS):
    receipt = call.data.split(":")[2]
    pay_status, _ = await CryptobotAPI(
        bot=bot, arSession=arSession, update=call
    ).bill_check(receipt)

    if pay_status == 0:
        data = await state.get_data()
        server, amount, account = data["server"], data["amount"], data["account"]
        await call.message.edit_text("Ура! Ваш заказ принят, ожидайте вирты в течение 10 минут.")
        for admin in get_admins():
            await bot.send_message(
                admin,
                f"Новый заказ\nСервер: {server}\nКол-во: {amount}\nСчёт: {account}\nОплата: CryptoBot",
            )
        await state.clear()
    elif pay_status == 2:
        await call.answer("Оплата не найдена. Попробуйте позже.", show_alert=True)
    elif pay_status == 3:
        await call.answer("Вы не успели оплатить счёт.", show_alert=True)
    else:
        await call.answer("Не удалось проверить оплату.", show_alert=True)


@router.callback_query(F.data.startswith("BuyPay:Yoomoney"), StateFilter("buy_wait_payment"))
async def check_yoomoney(call: CallbackQuery, state: FSM, bot: Bot, arSession: ARS):
    receipt = call.data.split(":")[2]
    pay_status, _ = await YoomoneyAPI(
        bot=bot, arSession=arSession, update=call
    ).bill_check(receipt)

    if pay_status == 0:
        data = await state.get_data()
        server, amount, account = data["server"], data["amount"], data["account"]
        await call.message.edit_text("Ура! Ваш заказ принят, ожидайте вирты в течение 10 минут.")
        for admin in get_admins():
            await bot.send_message(
                admin,
                f"Новый заказ\nСервер: {server}\nКол-во: {amount}\nСчёт: {account}\nОплата: YooMoney",
            )
        await state.clear()
    elif pay_status == 2:
        await call.answer("Оплата не найдена. Попробуйте позже.", show_alert=True)
    elif pay_status == 3:
        await call.answer("Оплата произведена не в рублях.", show_alert=True)
    else:
        await call.answer("Не удалось проверить оплату.", show_alert=True)


@router.message(F.successful_payment, StateFilter("buy_wait_payment"))
async def stars_success(message: Message, state: FSM, bot: Bot):
    data = await state.get_data()
    server, amount, account = data["server"], data["amount"], data["account"]
    await message.answer("Ура! Ваш заказ принят, ожидайте вирты в течение 10 минут.")
    for admin in get_admins():
        await bot.send_message(
            admin,
            f"Новый заказ\nСервер: {server}\nКол-во: {amount}\nСчёт: {account}\nОплата: Telegram Stars",
        )
    await state.clear()
