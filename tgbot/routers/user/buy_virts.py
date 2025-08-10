# - *- coding: utf-8 - *-
"""Flow for buying virtual currency with multiple payment methods."""
from math import ceil

from aiogram import Router, F, Bot
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, Message, LabeledPrice

from tgbot.data.config import get_admins
from tgbot.keyboards.inline_buy import (
    SERVERS,
    TOTAL_PAGES,
    back_menu_kb,
    alt_payment_methods_kb,
    payment_bill_kb,
    servers_kb,
)
from tgbot.services.api_cryptobot import CryptobotAPI
from tgbot.services.api_yoomoney import YoomoneyAPI
from tgbot.utils.misc.bot_models import FSM, ARS

router = Router(name=__name__)


def parse_amount(text: str) -> int:
    """Parse amount strings like 1.5кк, 500к or 1500000."""
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
    await call.message.edit_text(
        f"<b>Выберите сервер (Страница 1/{TOTAL_PAGES}):</b>",
        reply_markup=servers_kb(0),
    )


@router.callback_query(F.data.startswith("servers_page:"), StateFilter("buy_server"))
async def servers_page(call: CallbackQuery, state: FSM):
    page = int(call.data.split(":")[1])
    await call.message.edit_text(
        f"<b>Выберите сервер (Страница {page+1}/{TOTAL_PAGES}):</b>",
        reply_markup=servers_kb(page),
    )
    await call.answer()


@router.callback_query(F.data.startswith("server_select:"), StateFilter("buy_server"))
async def server_selected(call: CallbackQuery, state: FSM):
    idx = int(call.data.split(":")[1])
    server = SERVERS[idx]
    await state.update_data(server=server)
    await state.set_state("buy_amount")
    await call.message.edit_text(
        f"<b>Сервер {server}</b>\nВведите количество валюты (например 1кк):",
        reply_markup=back_menu_kb("buy_start"),
    )
    await call.answer()


@router.callback_query(F.data == "ignore")
async def ignore_cb(call: CallbackQuery):
    await call.answer()


@router.message(StateFilter("buy_amount"))
async def amount_input(message: Message, state: FSM):
    amount = parse_amount(message.text)
    if amount < 500_000:
        await message.answer(
            "Минимальная сумма покупки 0.5кк (500000). Попробуйте снова:",
            reply_markup=back_menu_kb("buy_start"),
        )
        return
    price = ceil(amount / 1_000_000 * 99)
    await state.update_data(amount=amount, price=price)
    await state.set_state("buy_account")
    await message.answer(
        "Введите ваш банковский счет:",
        reply_markup=back_menu_kb("buy_back_amount"),
    )


@router.message(StateFilter("buy_account"))
async def account_input(message: Message, state: FSM, bot: Bot):
    if not message.text.isdigit() or len(message.text) > 7:
        await message.answer(
            "Счет должен содержать только цифры и быть не длиннее 7 знаков. Введите снова:",
            reply_markup=back_menu_kb("buy_back_amount"),
        )
        return
    account = message.text
    data = await state.get_data()
    server = data["server"]
    amount = data["amount"]
    price = data["price"]
    await state.update_data(account=account)
    stars = ceil(price / 1.4)
    invoice = await bot.send_invoice(
        chat_id=message.chat.id,
        title="Покупка виртов",
        description=(
            f"Сервер: {server}\n"
            f"Количество: {amount}\n"
            f"Цена: {price} ₽\n"
            f"Счет: {account}"
        ),
        payload="buy_virts",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="Вирты", amount=stars)],
    )
    await state.update_data(invoice_msg=invoice.message_id)
    await message.answer(
        "Или выберите другой способ оплаты:",
        reply_markup=alt_payment_methods_kb(),
    )
    await state.set_state("buy_wait_payment")


@router.callback_query(F.data.startswith("pay_method:"), StateFilter("buy_wait_payment"))
async def payment_choose(call: CallbackQuery, state: FSM, bot: Bot, arSession: ARS):
    """Generate invoice for selected payment method."""
    method = call.data.split(":")[1]
    data = await state.get_data()
    price = data["price"]
    if method == "cryptobot":
        bill_message, bill_link, bill_receipt = await CryptobotAPI(
            bot=bot,
            arSession=arSession,
            update=call,
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
    else:
        bill_message, bill_link, bill_receipt = await YoomoneyAPI(
            bot=bot,
            arSession=arSession,
            update=call,
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


@router.callback_query(F.data == "buy_back_account", StateFilter("buy_wait_payment"))
async def buy_back_account(call: CallbackQuery, state: FSM, bot: Bot):
    data = await state.get_data()
    invoice_msg = data.get("invoice_msg")
    if invoice_msg:
        try:
            await bot.delete_message(call.from_user.id, invoice_msg)
        except Exception:
            pass
    await state.set_state("buy_account")
    await call.message.edit_text(
        "Введите ваш банковский счет:",
        reply_markup=back_menu_kb("buy_back_amount"),
    )
    await call.answer()


@router.callback_query(F.data == "buy_back_methods", StateFilter("buy_wait_payment"))
async def buy_back_methods(call: CallbackQuery, state: FSM):
    await call.message.edit_text(
        "Или выберите другой способ оплаты:",
        reply_markup=alt_payment_methods_kb(),
    )
    await call.answer()


@router.callback_query(F.data == "buy_back_amount", StateFilter("buy_account"))
async def buy_back_amount(call: CallbackQuery, state: FSM):
    await state.set_state("buy_amount")
    await call.message.edit_text(
        "Введите количество валюты (например 1кк):",
        reply_markup=back_menu_kb("buy_start"),
    )
    await call.answer()


@router.callback_query(F.data.startswith("BuyPay:Cryptobot"), StateFilter("buy_wait_payment"))
async def check_cryptobot(call: CallbackQuery, state: FSM, bot: Bot, arSession: ARS):
    receipt = call.data.split(":")[2]
    pay_status, _ = await CryptobotAPI(
        bot=bot,
        arSession=arSession,
        update=call,
    ).bill_check(receipt)
    if pay_status == 0:
        data = await state.get_data()
        server, amount, account = data["server"], data["amount"], data["account"]
        await call.message.edit_text("Ура! Ваш заказ принят, ожидайте вирты в течении 10 минут.")
        for admin in get_admins():
            await bot.send_message(
                admin,
                f"Новый заказ\nСервер: {server}\nКол-во: {amount}\nСчёт: {account}\nОплата: CryptoBot",
            )
        await state.clear()
    elif pay_status == 2:
        await call.answer("Оплата не найдена. Попробуйте позже.", True)
    elif pay_status == 3:
        await call.answer("Вы не успели оплатить счёт.", True)
    else:
        await call.answer("Не удалось проверить оплату.", True)


@router.callback_query(F.data.startswith("BuyPay:Yoomoney"), StateFilter("buy_wait_payment"))
async def check_yoomoney(call: CallbackQuery, state: FSM, bot: Bot, arSession: ARS):
    receipt = call.data.split(":")[2]
    pay_status, _ = await YoomoneyAPI(
        bot=bot,
        arSession=arSession,
        update=call,
    ).bill_check(receipt)
    if pay_status == 0:
        data = await state.get_data()
        server, amount, account = data["server"], data["amount"], data["account"]
        await call.message.edit_text("Ура! Ваш заказ принят, ожидайте вирты в течении 10 минут.")
        for admin in get_admins():
            await bot.send_message(
                admin,
                f"Новый заказ\nСервер: {server}\nКол-во: {amount}\nСчёт: {account}\nОплата: YooMoney",
            )
        await state.clear()
    elif pay_status == 2:
        await call.answer("Оплата не найдена. Попробуйте позже.", True)
    elif pay_status == 3:
        await call.answer("Оплата произведена не в рублях.", True)
    else:
        await call.answer("Не удалось проверить оплату.", True)


@router.message(F.successful_payment, StateFilter("buy_wait_payment"))
async def stars_success(message: Message, state: FSM, bot: Bot):
    data = await state.get_data()
    server, amount, account = data["server"], data["amount"], data["account"]
    await message.answer("Ура! Ваш заказ принят, ожидайте вирты в течении 10 минут.")
    for admin in get_admins():
        await bot.send_message(
            admin,
            f"Новый заказ\nСервер: {server}\nКол-во: {amount}\nСчёт: {account}\nОплата: Telegram Stars",
        )
    await state.clear()

