from __future__ import annotations

from dataclasses import dataclass

from bot.handlers.admin import format_admin_stats, format_whoami


@dataclass(slots=True)
class TelegramUser:
    id: int
    username: str | None = "tester"
    first_name: str | None = "Test"


def test_format_admin_stats_handles_empty_tracking_sections() -> None:
    text = format_admin_stats(
        total_users=3,
        notifications_users=2,
        daily_digest_users=1,
        watchlist_items=4,
        topics_count=5,
        market_opens_today=0,
        market_opens_total=0,
        alerts_sent_today=0,
        snapshots_count=12,
        top_clicked_markets=[],
        top_search_queries=[],
    )

    assert "Total users: 3" in text
    assert "Market opens today: 0" in text
    assert text.count("not tracked yet") == 2


def test_format_admin_stats_includes_top_markets_and_queries() -> None:
    text = format_admin_stats(
        total_users=1,
        notifications_users=0,
        daily_digest_users=0,
        watchlist_items=0,
        topics_count=0,
        market_opens_today=2,
        market_opens_total=7,
        alerts_sent_today=1,
        snapshots_count=9,
        top_clicked_markets=[("m1", "Bitcoin market", 4)],
        top_search_queries=[("bitcoin", 3)],
    )

    assert "1. Bitcoin market" in text
    assert "1. bitcoin" in text


def test_format_whoami_shows_user_identity_without_secrets() -> None:
    text = format_whoami(TelegramUser(id=123456789, username="pulse", first_name="Ilyas"))

    assert "👤 Your Telegram ID:\n123456789" in text
    assert "Username:\n@pulse" in text
    assert "First name:\nIlyas" in text
    assert "BOT_TOKEN" not in text


def test_format_whoami_handles_missing_username() -> None:
    text = format_whoami(TelegramUser(id=1, username=None, first_name=None))

    assert "Username:\nnot set" in text
    assert "First name:\nnot set" in text
