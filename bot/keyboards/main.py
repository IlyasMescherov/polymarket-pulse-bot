from __future__ import annotations

from typing import Any

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.services.market_analyzer import CATEGORY_LABELS
from bot.utils.i18n import normalize_language


HOT_MARKETS = "markets:hot"
NEW_MARKETS = "markets:new"
TODAY_PULSE = "markets:today"
SHARP_MOVES = "markets:moves"
MARKET_SEARCH = "markets:search"
WATCHLIST_VIEW = "watchlist:view"
CATEGORIES = "categories:open"
SETTINGS_MENU = "settings:open"
MY_NOTIFICATIONS = "settings:notifications"
ABOUT_PROJECT = "menu:about"
QUICK_START = "menu:quick_start"
QUICK_START_OK = "menu:quick_start:ok"
SHARE_BOT = "menu:share"
BACK_TO_MENU = "menu:back"

WATCHLIST_ADD_PREFIX = "watchlist:add:"
WATCHLIST_REMOVE_PREFIX = "watchlist:remove:"
EXPLAIN_PREFIX = "market:explain:"
RESOLUTION_PREFIX = "market:resolution:"
TIMELINE_PREFIX = "market:timeline:"
WHY_MOVED_PREFIX = "market:why_moved:"
SHARE_MARKET_PREFIX = "market:share:"
OPEN_MARKET_PREFIX = "market:open:"
CATEGORY_PREFIX = "categories:select:"
TOPICS_MENU = "settings:topics"
TOPIC_ADD = "topics:add"
TOPIC_REMOVE_PREFIX = "topics:remove:"

NOTIFICATIONS_ON = "settings:notifications:on"
NOTIFICATIONS_OFF = "settings:notifications:off"
DAILY_DIGEST_ON = "settings:daily:on"
DAILY_DIGEST_OFF = "settings:daily:off"
LANGUAGE_RU = "settings:language:ru"
LANGUAGE_EN = "settings:language:en"
THRESHOLD_PREFIX = "settings:threshold:"
MIN_VOLUME_PREFIX = "settings:min_volume:"

LABELS: dict[str, dict[str, str]] = {
    "ru": {
        "quick_start": "🚀 Быстрый старт",
        "hot": "🔥 Горячие",
        "new": "🆕 Новые",
        "today": "📰 Пульс дня",
        "moves": "📈 Движения",
        "search": "🔍 Поиск",
        "watchlist": "⭐ Watchlist",
        "categories": "🗂 Категории",
        "notifications": "🔔 Уведомления",
        "settings": "⚙️ Настройки",
        "share": "🤝 Поделиться",
        "about": "ℹ️ О проекте",
        "understood": "Понятно",
        "open_market": "🔗 Открыть",
        "add_watchlist": "⭐ В Watchlist",
        "explain": "🧠 Просто",
        "resolution": "📜 Правила",
        "timeline": "📊 Динамика",
        "why_moved": "🧭 Почему двигается",
        "share_market": "📤 Поделиться",
        "remove": "🗑 Удалить",
        "back": "Назад в меню",
        "topics": "🎯 Мои темы",
        "add_topic": "➕ Добавить тему",
    },
    "en": {
        "quick_start": "🚀 Quick Start",
        "hot": "🔥 Hot",
        "new": "🆕 New",
        "today": "📰 Today’s Pulse",
        "moves": "📈 Moves",
        "search": "🔍 Search",
        "watchlist": "⭐ Watchlist",
        "categories": "🗂 Categories",
        "notifications": "🔔 Alerts",
        "settings": "⚙️ Settings",
        "share": "🤝 Share",
        "about": "ℹ️ About",
        "understood": "Got it",
        "open_market": "🔗 Open",
        "add_watchlist": "⭐ Watchlist",
        "explain": "🧠 Simple",
        "resolution": "📜 Rules",
        "timeline": "📊 Timeline",
        "why_moved": "🧭 Why it moved",
        "share_market": "📤 Share",
        "remove": "🗑 Remove",
        "back": "Back to Menu",
        "topics": "🎯 My topics",
        "add_topic": "➕ Add topic",
    },
}


def label(key: str, language: str | None = None) -> str:
    normalized = normalize_language(language)
    return LABELS[normalized].get(key, LABELS["ru"].get(key, key))


def main_menu_keyboard(language: str | None = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=label("hot", language), callback_data=HOT_MARKETS)
    builder.button(text=label("new", language), callback_data=NEW_MARKETS)
    builder.button(text=label("today", language), callback_data=TODAY_PULSE)
    builder.button(text=label("moves", language), callback_data=SHARP_MOVES)
    builder.button(text=label("search", language), callback_data=MARKET_SEARCH)
    builder.button(text=label("watchlist", language), callback_data=WATCHLIST_VIEW)
    builder.button(text=label("categories", language), callback_data=CATEGORIES)
    builder.button(text=label("notifications", language), callback_data=MY_NOTIFICATIONS)
    builder.button(text=label("quick_start", language), callback_data=QUICK_START)
    builder.button(text=label("settings", language), callback_data=SETTINGS_MENU)
    builder.button(text=label("share", language), callback_data=SHARE_BOT)
    builder.button(text=label("about", language), callback_data=ABOUT_PROJECT)
    builder.adjust(2)
    return builder.as_markup()


def quick_start_keyboard(language: str | None = None) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=label("understood", language),
                    callback_data=QUICK_START_OK,
                )
            ]
        ]
    )


def market_actions_keyboard(
    url: str,
    market_id: str,
    language: str | None = None,
    source: str = "hot",
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=label("open_market", language),
                    callback_data=f"{OPEN_MARKET_PREFIX}{source}:{market_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=label("add_watchlist", language),
                    callback_data=f"{WATCHLIST_ADD_PREFIX}{market_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=label("explain", language),
                    callback_data=f"{EXPLAIN_PREFIX}{market_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=label("resolution", language),
                    callback_data=f"{RESOLUTION_PREFIX}{market_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=label("timeline", language),
                    callback_data=f"{TIMELINE_PREFIX}{market_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=label("why_moved", language),
                    callback_data=f"{WHY_MOVED_PREFIX}{market_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=label("share_market", language),
                    callback_data=f"{SHARE_MARKET_PREFIX}{market_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=label("back", language),
                    callback_data=BACK_TO_MENU,
                )
            ],
        ]
    )


def market_link_keyboard(url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=label("open_market"), url=url)],
            [InlineKeyboardButton(text=label("back"), callback_data=BACK_TO_MENU)],
        ]
    )


def watchlist_item_keyboard(
    item_id: int,
    market_id: str,
    url: str,
    language: str | None = None,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=label("open_market", language),
                    callback_data=f"{OPEN_MARKET_PREFIX}watchlist:{market_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=label("explain", language),
                    callback_data=f"{EXPLAIN_PREFIX}{market_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=label("resolution", language),
                    callback_data=f"{RESOLUTION_PREFIX}{market_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=label("timeline", language),
                    callback_data=f"{TIMELINE_PREFIX}{market_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=label("remove", language),
                    callback_data=f"{WATCHLIST_REMOVE_PREFIX}{item_id}",
                )
            ],
        ]
    )


def categories_keyboard(language: str | None = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key, name in CATEGORY_LABELS.items():
        builder.button(text=name, callback_data=f"{CATEGORY_PREFIX}{key}")
    builder.button(text=label("back", language), callback_data=BACK_TO_MENU)
    builder.adjust(2)
    return builder.as_markup()


def settings_keyboard(user: Any, language: str | None = None) -> InlineKeyboardMarkup:
    notifications_status = "ON" if user.notifications_enabled else "OFF"
    daily_status = "ON" if user.daily_digest_enabled else "OFF"
    threshold = int(user.movement_threshold * 100)

    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"🔔 Sharp moves alerts: {notifications_status}",
        callback_data=NOTIFICATIONS_OFF
        if user.notifications_enabled
        else NOTIFICATIONS_ON,
    )
    builder.button(
        text=f"📰 Daily digest: {daily_status}",
        callback_data=DAILY_DIGEST_OFF
        if user.daily_digest_enabled
        else DAILY_DIGEST_ON,
    )
    builder.button(text=label("topics", language), callback_data=TOPICS_MENU)
    builder.button(text="🌍 Language: RU", callback_data=LANGUAGE_RU)
    builder.button(text="🌍 Language: EN", callback_data=LANGUAGE_EN)
    for value in (5, 10, 15, 20):
        marker = "✓ " if threshold == value else ""
        builder.button(
            text=f"📊 {marker}Movement threshold: {value}%",
            callback_data=f"{THRESHOLD_PREFIX}{value}",
        )
    min_volume = int(getattr(user, "min_volume_for_alerts", 0) or 0)
    for value in (0, 10_000, 50_000, 100_000):
        marker = "✓ " if min_volume == value else ""
        label_value = "$0" if value == 0 else f"${value // 1000}K"
        builder.button(
            text=f"🔎 {marker}Min alert volume: {label_value}",
            callback_data=f"{MIN_VOLUME_PREFIX}{value}",
        )
    builder.button(text=label("back", language), callback_data=BACK_TO_MENU)
    builder.adjust(1)
    return builder.as_markup()


def topics_keyboard(topics: list[Any], language: str | None = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=label("add_topic", language), callback_data=TOPIC_ADD)
    for topic in topics:
        builder.button(
            text=f"🗑 {topic.topic}",
            callback_data=f"{TOPIC_REMOVE_PREFIX}{topic.id}",
        )
    builder.button(text=label("back", language), callback_data=SETTINGS_MENU)
    builder.adjust(1)
    return builder.as_markup()


def notifications_keyboard(enabled: bool, language: str | None = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if enabled:
        builder.button(text="🔕 Выключить уведомления", callback_data=NOTIFICATIONS_OFF)
    else:
        builder.button(text="🔔 Включить уведомления", callback_data=NOTIFICATIONS_ON)
    builder.button(text=label("back", language), callback_data=BACK_TO_MENU)
    builder.adjust(1)
    return builder.as_markup()
