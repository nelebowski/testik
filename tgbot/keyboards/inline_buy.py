# - *- coding: utf-8 - *-
"""Inline keyboards for buying virtual currency."""
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from tgbot.utils.const_functions import ikb

SERVERS = [f"Сервер {i}" for i in range(1, 90)]
PER_PAGE = 25


def servers_kb(page: int = 0) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    start = page * PER_PAGE
    end = min(start + PER_PAGE, len(SERVERS))
    for idx, server in enumerate(SERVERS[start:end], start=start):
        builder.row(ikb(server, data=f"server_select:{idx}"))

    nav = []
    if page > 0:
        nav.append(ikb("⬅️ Назад", data=f"servers_page:{page-1}"))
    nav.append(ikb("🔙 В меню", data="back_to_menu"))
    if end < len(SERVERS):
        nav.append(ikb("Вперед ➡️", data=f"servers_page:{page+1}"))
    if nav:
        builder.row(*nav)
    return builder.as_markup()


def payment_methods_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(ikb("Cryptobot", data="pay_method:cryptobot"))
    builder.row(ikb("ЮMoney", data="pay_method:yoomoney"))
    builder.row(ikb("Telegram Stars", data="pay_method:stars"))
    builder.row(ikb("🔙 В меню", data="back_to_menu"))
    return builder.as_markup()
