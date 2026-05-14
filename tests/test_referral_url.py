from __future__ import annotations

from bot.config import load_settings


def test_referral_url_and_admin_ids_are_loaded_from_environment(monkeypatch) -> None:
    load_settings.cache_clear()
    monkeypatch.setenv("BOT_TOKEN", "test-token")
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("POLYMARKET_REFERRAL_URL", "https://polymarket.com/?ref=pulse")
    monkeypatch.setenv("PROJECT_CHANNEL_URL", "https://t.me/PulseMarketAI")
    monkeypatch.setenv("PROJECT_SUPPORT_URL", "https://t.me/PulseMarketAIHelp")
    monkeypatch.setenv("PROJECT_X_URL", "https://x.com/PulseMarketBot")
    monkeypatch.setenv("ADMIN_TELEGRAM_IDS", "123, bad, 456,,")

    settings = load_settings()

    assert settings.polymarket_referral_url == "https://polymarket.com/?ref=pulse"
    assert settings.project_channel_url == "https://t.me/PulseMarketAI"
    assert settings.project_support_url == "https://t.me/PulseMarketAIHelp"
    assert settings.project_x_url == "https://x.com/PulseMarketBot"
    assert settings.admin_telegram_ids == frozenset({123, 456})

    load_settings.cache_clear()
