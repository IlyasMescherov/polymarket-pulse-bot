from __future__ import annotations

from datetime import datetime, timedelta, timezone

from bot.services.polymarket_client import Market
from bot.services.today_pulse import build_today_pulse_items
from bot.utils.formatting import format_channel_digest


def test_channel_digest_contains_safety_scope_and_bot_link() -> None:
    market = Market(
        id="btc",
        question="Will Bitcoin hit $150k?",
        slug="will-bitcoin-hit-150k",
        yes_probability=0.63,
        volume=120_000,
        end_date=datetime.now(timezone.utc) + timedelta(days=30),
        url="https://polymarket.com/market/will-bitcoin-hit-150k",
        raw={},
    )
    items = build_today_pulse_items([market], limit=1, language="en")

    text = format_channel_digest(items, language="en")

    assert "📰 Today’s Pulse" in text
    assert "Will Bitcoin hit $150k?" in text
    assert "No trading. No wallets. No financial advice." in text
    assert "https://t.me/PulseMarketAIBot" in text
