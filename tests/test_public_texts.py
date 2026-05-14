from __future__ import annotations

from bot.config import load_settings
from bot.handlers.menu import _about_lines, _share_lines


def test_about_lines_include_public_links(monkeypatch) -> None:
    load_settings.cache_clear()
    monkeypatch.setenv("BOT_TOKEN", "test-token")
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("PROJECT_TELEGRAM_HANDLE", "@PulseMarketAIBot")
    monkeypatch.setenv("PROJECT_CHANNEL_URL", "https://t.me/PulseMarketAI")
    monkeypatch.setenv("PROJECT_SUPPORT_URL", "https://t.me/PulseMarketAIHelp")
    monkeypatch.setenv("PROJECT_X_URL", "https://x.com/PulseMarketBot")

    settings = load_settings()
    text = "\n".join(_about_lines(settings, "en"))

    assert "GitHub: https://github.com/IlyasMescherov/polymarket-pulse-bot" in text
    assert "Bot: https://t.me/PulseMarketAIBot" in text
    assert "Channel: https://t.me/PulseMarketAI" in text
    assert "Support: https://t.me/PulseMarketAIHelp" in text
    assert "X/Twitter: https://x.com/PulseMarketBot" in text
    assert "No financial advice." in text

    load_settings.cache_clear()


def test_share_lines_skip_empty_public_links(monkeypatch) -> None:
    load_settings.cache_clear()
    monkeypatch.setenv("BOT_TOKEN", "test-token")
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("PROJECT_CHANNEL_URL", "")
    monkeypatch.setenv("PROJECT_SUPPORT_URL", "")
    monkeypatch.setenv("PROJECT_X_URL", "")

    settings = load_settings()
    text = "\n".join(_share_lines(settings, "en"))

    assert "Share PulseMarket AI" in text
    assert "Updates:" not in text
    assert "Support:" not in text
    assert "X/Twitter:" not in text
    assert "No financial advice." in text

    load_settings.cache_clear()
