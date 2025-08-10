# - *- coding: utf-8 - *-
"""Inline keyboards for buying virtual currency."""
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from math import ceil

from tgbot.utils.const_functions import ikb

SERVERS = [f"Сервер {i}" for i in range(1, 90)]
PER_PAGE = 24
TOTAL_PAGES = ceil(len(SERVERS) / PER_PAGE)


def servers_kb(page: int = 0) -> InlineKeyboardMarkup:
    """Return keyboard with servers in a 3-column grid."""
    builder = InlineKeyboardBuilder()
    start = page * PER_PAGE
    end = min(start + PER_PAGE, len(SERVERS))

    buttons = [
        ikb(server, data=f"server_select:{idx}")
        for idx, server in enumerate(SERVERS[start:end], start=start)
    ]
    for i in range(0, len(buttons), 3):
        builder.row(*buttons[i:i + 3])

    nav = []
    if page > 0:
        nav.append(ikb("⬅️", data=f"servers_page:{page-1}"))
    nav.append(ikb(f"{page + 1}/{TOTAL_PAGES}", data="ignore"))
    if end < len(SERVERS):
        nav.append(ikb("➡️", data=f"servers_page:{page+1}"))
    builder.row(*nav)
    builder.row(ikb("🔙 В меню", data="back_to_menu"))
    return builder.as_markup()


def back_menu_kb(back: str) -> InlineKeyboardMarkup:
    """Keyboard with back and menu buttons."""
    builder = InlineKeyboardBuilder()
    builder.row(ikb("⬅️ Назад", data=back))
    builder.row(ikb("🔙 В меню", data="back_to_menu"))
    return builder.as_markup()


def alt_payment_methods_kb() -> InlineKeyboardMarkup:
    """Alternative payment methods when Stars invoice is shown separately."""
    builder = InlineKeyboardBuilder()
    builder.row(ikb("Cryptobot", data="pay_method:cryptobot"))
    builder.row(ikb("ЮMoney", data="pay_method:yoomoney"))
    builder.row(ikb("⬅️ Назад", data="buy_back_account"))
    builder.row(ikb("🔙 В меню", data="back_to_menu"))
    return builder.as_markup()


def payment_bill_kb(link: str, receipt: str, method: str) -> InlineKeyboardMarkup:
    """Keyboard with link and check button for generated invoices."""
    builder = InlineKeyboardBuilder()
    builder.row(ikb("🌀 Перейти к оплате", url=link))
    builder.row(ikb("🔄 Проверить оплату", data=f"BuyPay:{method}:{receipt}"))
    builder.row(ikb("⬅️ Назад", data="buy_back_methods"))
    builder.row(ikb("🔙 В меню", data="back_to_menu"))
    return builder.as_markup()
