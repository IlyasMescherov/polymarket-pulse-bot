from __future__ import annotations

from bot.utils.i18n import normalize_language, t


def test_i18n_defaults_to_ru() -> None:
    assert normalize_language(None) == "ru"
    assert normalize_language("unknown") == "ru"


def test_i18n_returns_english_text() -> None:
    text = t("dashboard", "en")
    assert "PulseMarket AI helps you understand what matters on Polymarket." in text
    assert "Today’s Pulse" in text
    assert "Activity Radar" in text
    assert "Research only · No trade execution" in text


def test_i18n_start_text_explains_first_actions() -> None:
    ru_text = t("dashboard", "ru")

    assert "Начни отсюда:" in ru_text
    assert "Короткая подборка рынков" in ru_text
    assert "Радар активности" in ru_text
    assert "Поиск" in ru_text


def test_i18n_falls_back_to_key() -> None:
    assert t("missing.key", "ru") == "missing.key"
