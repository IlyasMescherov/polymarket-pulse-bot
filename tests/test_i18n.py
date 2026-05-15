from __future__ import annotations

from bot.utils.i18n import normalize_language, t


def test_i18n_defaults_to_ru() -> None:
    assert normalize_language(None) == "ru"
    assert normalize_language("unknown") == "ru"


def test_i18n_returns_english_text() -> None:
    text = t("dashboard", "en")
    assert "daily Polymarket intelligence companion" in text
    assert "See what matters today" in text
    assert "Spot where attention is rising" in text
    assert "Research only · No trade execution" in text


def test_i18n_start_text_explains_first_actions() -> None:
    ru_text = t("dashboard", "ru")

    assert "ежедневный помощник" in ru_text
    assert "увидеть, что сегодня важно" in ru_text
    assert "где растёт внимание" in ru_text
    assert "понять любой рынок" in ru_text


def test_i18n_falls_back_to_key() -> None:
    assert t("missing.key", "ru") == "missing.key"
