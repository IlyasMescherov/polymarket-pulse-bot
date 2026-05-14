from __future__ import annotations

from bot.utils.i18n import normalize_language, t


def test_i18n_defaults_to_ru() -> None:
    assert normalize_language(None) == "ru"
    assert normalize_language("unknown") == "ru"


def test_i18n_returns_english_text() -> None:
    assert "No trading" in t("dashboard", "en")


def test_i18n_falls_back_to_key() -> None:
    assert t("missing.key", "ru") == "missing.key"
