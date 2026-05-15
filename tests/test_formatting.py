from __future__ import annotations

from datetime import datetime, timezone

from bot.services.polymarket_client import Market
from bot.utils.formatting import (
    format_beginner_explanation,
    format_date,
    format_market_card,
    format_market_timeline,
    format_probability,
    format_share_market_card,
    format_usd,
)


def test_format_probability_handles_missing_data() -> None:
    assert format_probability(None) == "данных пока нет"


def test_format_probability_explains_very_low_values() -> None:
    assert format_probability(0, "en") == "Unlikely"
    assert format_probability(0.004, "en") == "<1%"
    assert format_probability(0, "ru") == "Маловероятно"


def test_format_usd_compacts_large_values() -> None:
    assert format_usd(1_250_000) == "$1.2M"
    assert format_usd(120_000) == "$120,000"


def test_market_card_contains_core_fields() -> None:
    market = Market(
        id="1",
        question="Will this test pass?",
        slug="will-this-test-pass",
        yes_probability=0.63,
        volume=120_000,
        end_date=datetime(2026, 6, 1, tzinfo=timezone.utc),
        url="https://polymarket.com/market/will-this-test-pass",
        raw={},
    )

    card = format_market_card(market)

    assert "Will this test pass?" in card
    assert "63%" in card
    assert "$120K" in card
    assert "До завершения:" in card
    assert "Настроение рынка:" in card


def test_market_card_supports_english_demo_labels() -> None:
    market = Market(
        id="1",
        question="Will this test pass?",
        slug="will-this-test-pass",
        yes_probability=0.63,
        volume=120_000,
        end_date=datetime(2026, 6, 1, tzinfo=timezone.utc),
        url="https://polymarket.com/market/will-this-test-pass",
        raw={},
    )

    card = format_market_card(market, heading="🔥 Hot market", language="en")
    beginner = format_beginner_explanation(market, language="en")
    share = format_share_market_card(market, language="en")

    assert "Title:" in card
    assert "Probability:" in card
    assert "Time left:" in card
    assert "Market Mood:" in card
    assert "🧠 Explain simply" in beginner
    assert "This market asks whether a specific event will happen." in beginner
    assert "📤 Polymarket market" in share


def test_format_date_handles_missing_data() -> None:
    assert format_date(None) == "данных пока нет"
    assert format_date(None, "en") == "data not available yet"


def test_timeline_formatting_handles_missing_history() -> None:
    assert "Пока мало данных" in format_market_timeline([])
    assert "Not enough data yet" in format_market_timeline([], language="en")
