from __future__ import annotations

from datetime import datetime, timedelta, timezone

from bot.services.market_mood import calculate_market_mood
from bot.services.polymarket_client import Market


def _market(volume: float = 1_000, hours: int = 240) -> Market:
    return Market(
        id="mood",
        question="Will this market be active?",
        slug="will-this-market-be-active",
        yes_probability=0.5,
        volume=volume,
        end_date=datetime.now(timezone.utc) + timedelta(hours=hours),
        url="https://polymarket.com/market/will-this-market-be-active",
        raw={},
    )


def test_market_mood_labels_are_human_readable() -> None:
    assert calculate_market_mood(_market(), language="en").label == "Quiet"
    assert calculate_market_mood(_market(volume=120_000), language="en").label == "Active"
    assert calculate_market_mood(_market(volume=600_000), language="en").label == "Heating up"
    assert calculate_market_mood(_market(), delta=0.12, language="en").label == "Volatile"
    assert calculate_market_mood(_market(hours=3), language="en").label == "Ending soon"


def test_market_mood_is_localized() -> None:
    mood = calculate_market_mood(_market(volume=120_000), language="ru")

    assert mood.label == "Активно"
    assert "Публичное внимание" in mood.reason
