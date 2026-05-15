from __future__ import annotations

from datetime import datetime, timedelta, timezone

from bot.services.content_publisher import (
    content_hash,
    format_smart_money_channel_post,
    format_today_pulse_channel_post,
    format_x_today_pulse_draft,
)
from bot.services.polymarket_client import Market
from bot.services.smart_money_analyzer import MarketActivity
from bot.services.today_pulse import build_today_pulse_items


def _market(market_id: str, title: str, probability: float = 0.63) -> Market:
    return Market(
        id=market_id,
        question=title,
        slug=market_id,
        yes_probability=probability,
        volume=120_000,
        end_date=datetime.now(timezone.utc) + timedelta(days=14),
        url=f"https://polymarket.com/market/{market_id}",
        raw={},
    )


def test_today_pulse_channel_post_is_english_first_and_safe() -> None:
    items = build_today_pulse_items(
        [_market("btc", "Will Bitcoin hit $150k?")],
        limit=1,
        language="en",
    )

    text = format_today_pulse_channel_post(items)

    assert text is not None
    assert "📰 Today’s Pulse" in text
    assert "Polymarket markets worth watching today" in text
    assert "Why people care:" in text
    assert "No trading. No wallets. No financial advice." in text
    assert "@PulseMarketAIBot" in text
    assert "Без" not in text
    assert "данных" not in text


def test_smart_money_channel_post_returns_none_without_data() -> None:
    assert format_smart_money_channel_post([]) is None


def test_smart_money_channel_post_has_required_safety_text() -> None:
    text = format_smart_money_channel_post(
        [
            MarketActivity(
                market_id="m1",
                market_title="Will crypto market activity rise?",
                amount_usd=25_000,
                trades_count=3,
                participant_count=2,
            )
        ]
    )

    assert text is not None
    assert "Activity Radar" in text
    assert "Public activity:" in text
    assert "Why people care:" in text
    assert "No trading. No wallets. No financial advice." in text
    lowered = text.lower()
    for phrase in (
        "insider",
        "inside information",
        "guaranteed profit",
        "buy now",
        "sell now",
        "copy this trader",
        "trade signal",
    ):
        assert phrase not in lowered


def test_x_today_pulse_draft_is_short_and_manual_safe() -> None:
    items = build_today_pulse_items(
        [
            _market("btc", "Will Bitcoin hit $150k by December 31, 2026?"),
            _market("eth", "Will Ethereum reach a new all time high in 2026?", 0.42),
        ],
        limit=2,
        language="en",
    )

    draft = format_x_today_pulse_draft(items)

    assert draft is not None
    assert len(draft) <= 280
    assert "No trading" in draft
    assert "No financial advice" in draft


def test_content_hash_is_stable_for_same_text() -> None:
    assert content_hash(" hello ") == content_hash("hello")
