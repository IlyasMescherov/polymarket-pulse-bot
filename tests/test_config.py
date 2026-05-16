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
    monkeypatch.delenv("NEWS_REFRESH_MINUTES", raising=False)
    monkeypatch.delenv("ENABLE_X_SOURCE", raising=False)
    monkeypatch.delenv("ENABLE_TELEGRAM_SOURCE", raising=False)
    monkeypatch.delenv("ENABLE_RSS_SOURCE", raising=False)
    monkeypatch.delenv("ENABLE_OFFICIAL_SOURCES", raising=False)
    monkeypatch.delenv("TODAY_REFRESH_MINUTES", raising=False)
    monkeypatch.delenv("TODAY_CACHE_TTL_SECONDS", raising=False)
    monkeypatch.delenv("TODAY_STALE_MAX_SECONDS", raising=False)
    monkeypatch.delenv("ENABLE_TODAY_BACKGROUND_REFRESH", raising=False)
    monkeypatch.delenv("OPENAI_REQUEST_TIMEOUT_SECONDS", raising=False)
    load_settings.cache_clear()
    try:
        settings = load_settings()
    finally:
        load_settings.cache_clear()

    assert settings.auto_channel_posting_enabled is False
    assert settings.x_drafts_enabled is True
    assert settings.x_posting_mode == "draft"
    assert settings.openai_model == "gpt-4o-mini"
    assert settings.news_refresh_minutes == 10
    assert settings.enable_x_source is False
    assert settings.enable_telegram_source is False
    assert settings.enable_rss_source is True
    assert settings.enable_official_sources is True
    assert settings.today_refresh_minutes == 5
    assert settings.today_cache_ttl_seconds == 300
    assert settings.today_stale_max_seconds == 3600
    assert settings.enable_today_background_refresh is True
    assert settings.openai_request_timeout_seconds == 10


def test_openai_model_env(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_MODEL", "gpt-test")
    load_settings.cache_clear()
    try:
        settings = load_settings()
    finally:
        load_settings.cache_clear()

    assert settings.openai_model == "gpt-test"


def test_project_channel_id_falls_back_to_channel_url(monkeypatch) -> None:
    monkeypatch.delenv("PROJECT_CHANNEL_ID", raising=False)
    monkeypatch.setenv("PROJECT_CHANNEL_URL", "https://t.me/PulseMarketAI")
    load_settings.cache_clear()
    try:
        settings = load_settings()
    finally:
        load_settings.cache_clear()

    assert settings.project_channel_id == "@PulseMarketAI"
