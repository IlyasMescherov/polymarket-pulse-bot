from __future__ import annotations

from bot.keyboards.main import label


def test_short_russian_button_labels() -> None:
    assert label("hot", "ru") == "🔥 Горячие"
    assert label("new", "ru") == "🆕 Новые"
    assert label("today", "ru") == "📰 Пульс дня"
    assert label("smart_money", "ru") == "🧠 Smart Money"
    assert label("moves", "ru") == "📈 Движения"
    assert label("search", "ru") == "🔍 Поиск"
    assert label("open_market", "ru") == "🔗 Открыть"
    assert label("resolution", "ru") == "📜 Правила"
    assert label("why_moved", "ru") == "🧭 Почему двигается"
    assert label("explain", "ru") == "🧠 Просто"
    assert label("share_market", "ru") == "📤 Поделиться"


def test_short_english_button_labels() -> None:
    assert label("hot", "en") == "🔥 Hot"
    assert label("new", "en") == "🆕 New"
    assert label("today", "en") == "📰 Today’s Pulse"
    assert label("smart_money", "en") == "🧠 Smart Money"
    assert label("moves", "en") == "📈 Moves"
    assert label("search", "en") == "🔍 Search"
    assert label("open_market", "en") == "🔗 Open"
    assert label("resolution", "en") == "📜 Rules"
    assert label("why_moved", "en") == "🧭 Why it moved"
    assert label("explain", "en") == "🧠 Simple"
    assert label("timeline", "en") == "📊 Timeline"
