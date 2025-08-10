# -*- coding: utf-8 -*-
"""Inline keyboards for buying virtual currency."""
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from tgbot.utils.const_functions import ikb

SERVERS = [f"Сервер {i}" for i in range(1, 90)]
PER_PAGE = 25


def servers_kb(page: int = 0) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    total = len(SERVERS)
    if total == 0:
        builder.row(ikb("🔙 В меню", data="back_to_menu"))
        return builder.as_markup()

    # clamp page
    if page < 0:
        page = 0
    max_page = (total - 1) // PER_PAGE
    if page > max_page:
        page = max_page

    start = page * PER_PAGE
    end = min(start + PER_PAGE, total)

    for idx, server in enumerate(SERVERS[start:end], start=start):
        builder.button(text=server, callback_data=f"server_select:{idx}")
    builder.adjust(5)

    nav = []
    if page > 0:
        nav.append(ikb("⬅️ Назад", data=f"servers_page:{page-1}"))
    nav.append(ikb("🔙 В меню", data="back_to_menu"))
    if end < total:
        nav.append(ikb("Вперед ➡️", data=f"servers_page:{page+1}"))

    if nav:
        builder.row(*nav)

    return builder.as_markup()


def back_menu_kb(back: str) -> InlineKeyboardMarkup:
    """Keyboard with back and menu buttons."""
    builder = InlineKeyboardBuilder()
    builder.row(ikb("⬅️ Назад", data=back))
    builder.row(ikb("🔙 В меню", data="back_to_menu"))
    return builder.as_markup()


def payment_methods_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(ikb("Cryptobot", data="pay_method:cryptobot"))
    builder.row(ikb("ЮMoney", data="pay_method:yoomoney"))
    builder.row(ikb("Telegram Stars", data="pay_method:stars"))
    builder.row(ikb("🔙 В меню", data="back_to_menu"))
    return builder.as_markup()


def payment_bill_kb(link: str, receipt: str, method: str) -> InlineKeyboardMarkup:
    """Keyboard with link and check button for generated invoices."""
    builder = InlineKeyboardBuilder()
    builder.row(ikb("🌀 Перейти к оплате", url=link))
    builder.row(ikb("🔄 Проверить оплату", data=f"BuyPay:{method}:{receipt}"))
    builder.row(ikb("🔙 В меню", data="back_to_menu"))
    return builder.as_markup()
