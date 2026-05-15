from __future__ import annotations

from dataclasses import dataclass

from bot.keyboards.main import public_trader_keyboard, settings_keyboard, label


def test_short_russian_button_labels() -> None:
    assert label("hot", "ru") == "🔥 Горячие"
    assert label("new", "ru") == "🆕 Новые"
    assert label("today", "ru") == "📰 Пульс дня"
    assert label("smart_money", "ru") == "🧠 Радар внимания"
    assert label("moves", "ru") == "📈 Движения"
    assert label("search", "ru") == "🔍 Поиск"
    assert label("watchlist", "ru") == "⭐ Сохранённые"
    assert label("open_market", "ru") == "🔗 Открыть"
    assert label("resolution", "ru") == "📜 Правила"
    assert label("why_moved", "ru") == "🧭 Почему это важно"
    assert label("explain", "ru") == "🧠 Объяснить просто"
    assert label("share_market", "ru") == "📤 Поделиться"


def test_short_english_button_labels() -> None:
    assert label("hot", "en") == "🔥 Hot"
    assert label("new", "en") == "🆕 New"
    assert label("today", "en") == "📰 Today’s Briefing"
    assert label("smart_money", "en") == "🧠 Activity Radar"
    assert label("moves", "en") == "📈 Moves"
    assert label("search", "en") == "🔍 Search"
    assert label("watchlist", "en") == "⭐ Saved"
    assert label("open_market", "en") == "🔗 Open"
    assert label("resolution", "en") == "📜 Rules"
    assert label("why_moved", "en") == "🧭 Why this matters"
    assert label("explain", "en") == "🧠 Explain simply"
    assert label("timeline", "en") == "📊 Timeline"


def test_public_trader_keyboard_uses_full_wallet_in_callback() -> None:
    wallet = "0x1111111111111111111111111111111111111111"
    keyboard = public_trader_keyboard(wallet, "en")

    button = keyboard.inline_keyboard[0][0]
    assert button.text == "👀 Follow public activity"
    assert button.callback_data == f"smart:tw:{wallet}"


@dataclass(slots=True)
class SettingsUser:
    notifications_enabled: bool = False
    daily_digest_enabled: bool = True
    smart_money_alerts_enabled: bool = True
    movement_threshold: float = 0.10
    min_volume_for_alerts: float = 10_000


def test_settings_keyboard_localizes_smart_money_alerts() -> None:
    ru_texts = [
        button.text
        for row in settings_keyboard(SettingsUser(), "ru").inline_keyboard
        for button in row
    ]
    en_texts = [
        button.text
        for row in settings_keyboard(SettingsUser(), "en").inline_keyboard
        for button in row
    ]

    assert "🧠 Уведомления радара: ВКЛ" in ru_texts
    assert "🧠 Activity alerts: ON" in en_texts
