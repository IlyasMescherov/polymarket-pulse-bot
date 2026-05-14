from __future__ import annotations

from bot.config import load_settings


def test_smart_money_active_market_threshold_default(monkeypatch) -> None:
    monkeypatch.delenv("SMART_MONEY_ACTIVE_MARKET_MIN_USD", raising=False)
    load_settings.cache_clear()
    try:
        settings = load_settings()
    finally:
        load_settings.cache_clear()

    assert settings.smart_money_active_market_min_usd == 1000.0


def test_smart_money_active_market_threshold_env(monkeypatch) -> None:
    monkeypatch.setenv("SMART_MONEY_ACTIVE_MARKET_MIN_USD", "2500")
    load_settings.cache_clear()
    try:
        settings = load_settings()
    finally:
        load_settings.cache_clear()

    assert settings.smart_money_active_market_min_usd == 2500.0
