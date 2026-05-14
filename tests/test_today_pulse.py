from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from bot.database.models import MarketSnapshot
from bot.services.polymarket_client import Market
from bot.services.today_pulse import build_today_pulse_items, explain_why_it_matters


def _market(
    market_id: str,
    question: str,
    probability: float | None,
    volume: float | None,
    days: int,
) -> Market:
    return Market(
        id=market_id,
        question=question,
        slug=market_id,
        yes_probability=probability,
        volume=volume,
        end_date=datetime.now(timezone.utc) + timedelta(days=days),
        url=f"https://polymarket.com/market/{market_id}",
        raw={},
    )


def test_today_pulse_ranks_score_volume_and_movement() -> None:
    high = _market("high", "High activity market", 0.65, 600_000, 3)
    low = _market("low", "Low activity market", 0.50, 1_000, 60)
    moved = _market("moved", "Moved market", 0.75, 80_000, 2)
    snapshots = {
        "moved": MarketSnapshot(
            market_id="moved",
            question="Moved market",
            yes_probability=0.55,
        )
    }

    items = build_today_pulse_items([low, moved, high], snapshots, limit=3, language="en")

    assert [item.market.id for item in items][:2] == ["moved", "high"]
    assert items[0].delta == pytest.approx(0.20)
    assert "Why" not in items[0].why_it_matters


def test_today_pulse_filters_incomplete_data_when_better_markets_exist() -> None:
    complete = [_market(str(index), f"Complete {index}", 0.5, 100_000, 10) for index in range(3)]
    incomplete = _market("missing", "Missing probability", None, 1_000_000, 10)

    items = build_today_pulse_items([incomplete, *complete], limit=3, language="en")

    assert "missing" not in [item.market.id for item in items]


def test_why_it_matters_template_is_language_aware() -> None:
    market = _market("btc", "Bitcoin market", 0.7, 120_000, 2)
    item = build_today_pulse_items([market], limit=1, language="ru")[0]

    assert explain_why_it_matters(
        item.market,
        item.pulse_score,
        item.market_health,
        language="ru",
    ).startswith("Интересно:")
