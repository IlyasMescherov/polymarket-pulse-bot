from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


HOT_MARKETS = "markets:hot"
NEW_MARKETS = "markets:new"
SHARP_MOVES = "markets:moves"
MY_NOTIFICATIONS = "settings:notifications"
ABOUT_PROJECT = "menu:about"
BACK_TO_MENU = "menu:back"
NOTIFICATIONS_ON = "settings:notifications:on"
NOTIFICATIONS_OFF = "settings:notifications:off"


def main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Горячие рынки", callback_data=HOT_MARKETS)
    builder.button(text="Новые рынки", callback_data=NEW_MARKETS)
    builder.button(text="Резкие движения", callback_data=SHARP_MOVES)
    builder.button(text="Мои уведомления", callback_data=MY_NOTIFICATIONS)
    builder.button(text="О проекте", callback_data=ABOUT_PROJECT)
    builder.adjust(1)
    return builder.as_markup()


def market_link_keyboard(url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Открыть рынок", url=url)],
            [InlineKeyboardButton(text="Назад в меню", callback_data=BACK_TO_MENU)],
        ]
    )


def notifications_keyboard(enabled: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if enabled:
        builder.button(text="Выключить уведомления", callback_data=NOTIFICATIONS_OFF)
    else:
        builder.button(text="Включить уведомления", callback_data=NOTIFICATIONS_ON)
    builder.button(text="Назад в меню", callback_data=BACK_TO_MENU)
    builder.adjust(1)
    return builder.as_markup()

