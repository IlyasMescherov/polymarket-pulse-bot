from __future__ import annotations

from datetime import datetime, timedelta, timezone

from bot.services.market_health import calculate_market_health, market_health_label
from bot.services.polymarket_client import Market


def _market(volume: float | None, probability: float | None, end_date: datetime | None) -> Market:
    return Market(
        id="1",
        question="Will health scoring work?",
        slug=None,
        yes_probability=probability,
        volume=volume,
        end_date=end_date,
        url="https://polymarket.com",
        raw={},
    )


def test_market_health_uses_fallback_data_quality() -> None:
    now = datetime(2026, 5, 14, tzinfo=timezone.utc)
    health = calculate_market_health(
        _market(600_000, 0.62, now + timedelta(days=10)),
        now=now,
    )

    assert health.value == 85
    assert health.label == "Healthy"


def test_market_health_can_use_spread_and_depth() -> None:
    now = datetime(2026, 5, 14, tzinfo=timezone.utc)
    health = calculate_market_health(
        _market(120_000, 0.5, now + timedelta(days=3)),
        spread=0.01,
        orderbook_depth=15_000,
        now=now,
    )

    assert health.value == 88
    assert health.label == "Healthy"


def test_market_health_labels() -> None:
    assert market_health_label(20) == "Risky"
    assert market_health_label(60) == "Medium"
    assert market_health_label(80) == "Healthy"
