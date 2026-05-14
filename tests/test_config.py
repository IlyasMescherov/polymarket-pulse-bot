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


def test_auto_publishing_config_defaults(monkeypatch) -> None:
    monkeypatch.delenv("AUTO_CHANNEL_POSTING_ENABLED", raising=False)
    monkeypatch.delenv("X_DRAFTS_ENABLED", raising=False)
    load_settings.cache_clear()
    try:
        settings = load_settings()
    finally:
        load_settings.cache_clear()

    assert settings.auto_channel_posting_enabled is False
    assert settings.x_drafts_enabled is True
    assert settings.x_posting_mode == "draft"


def test_project_channel_id_falls_back_to_channel_url(monkeypatch) -> None:
    monkeypatch.delenv("PROJECT_CHANNEL_ID", raising=False)
    monkeypatch.setenv("PROJECT_CHANNEL_URL", "https://t.me/PulseMarketAI")
    load_settings.cache_clear()
    try:
        settings = load_settings()
    finally:
        load_settings.cache_clear()

    assert settings.project_channel_id == "@PulseMarketAI"
