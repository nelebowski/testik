# - *- coding: utf-8 - *-
"""Inline keyboards for main user menu."""
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from tgbot.utils.const_functions import ikb


def start_menu_finl() -> InlineKeyboardMarkup:
    """Keyboard shown to regular users on /start."""
    keyboard = InlineKeyboardBuilder()
    keyboard.row(ikb("Купить вирты", data="buy_start"))
    keyboard.row(ikb("Мои покупки", data="user_purchases"))
    keyboard.row(ikb("Отзывы", data="reviews_start"))
    keyboard.row(ikb("Поддержка", data="support_start"))
    return keyboard.as_markup()
