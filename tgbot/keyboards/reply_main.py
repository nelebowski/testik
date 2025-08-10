# - *- coding: utf- 8 - *-
from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from tgbot.data.config import get_admins
from tgbot.utils.const_functions import rkb


# Кнопки главного меню
def menu_frep(user_id: int) -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardBuilder()

    keyboard.row(
        rkb("👤 Профиль"), rkb("☎️ Поддержка"),
    )

    if user_id in get_admins():
        keyboard.row(
            rkb("📊 Статистика"),
        ).row(
            rkb("⚙️ Настройки"), rkb("🔆 Общие функции"), rkb("🔑 Платежные системы"),
        )

    return keyboard.as_markup(resize_keyboard=True)


# Кнопки платежных систем
def payments_frep() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardBuilder()

    keyboard.row(
        rkb("🔷 CryptoBot"), rkb("🔮 ЮMoney"),
    ).row(
        rkb("⭐️ Telegram Stars"),
    ).row(
        rkb("🔙 Главное меню"),
    )

    return keyboard.as_markup(resize_keyboard=True)


# Кнопки общих функций
def functions_frep() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardBuilder()

    keyboard.row(
        rkb("🔍 Поиск"), rkb("📢 Рассылка"),
    ).row(
        rkb("🔙 Главное меню"),
    )

    return keyboard.as_markup(resize_keyboard=True)


# Кнопки настроек
def settings_frep() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardBuilder()

    keyboard.row(
        rkb("🖍 Изменить данные"), rkb("🕹 Выключатели"),
    ).row(
        rkb("🔙 Главное меню"),
    )

    return keyboard.as_markup(resize_keyboard=True)
