from __future__ import annotations

from datetime import datetime, timedelta, timezone

from bot.database.models import MarketSnapshot
from bot.services.polymarket_client import Market
from bot.services.risk_flags import (
    ENDING_SOON,
    LOW_VOLUME,
    MISSING_DATA,
    SHARP_MOVE,
    VERY_VOLATILE,
    count_strong_snapshot_moves,
    market_risk_flags,
)


def _market(
    volume: float | None = 5000,
    probability: float | None = 0.4,
    end_date: datetime | None = None,
) -> Market:
    return Market(
        id="1",
        question="Will risk flags work?",
        slug=None,
        yes_probability=probability,
        volume=volume,
        end_date=end_date,
        url="https://polymarket.com",
        raw={},
    )


def test_risk_flags_returns_max_three_flags() -> None:
    now = datetime(2026, 5, 14, tzinfo=timezone.utc)
    flags = market_risk_flags(
        _market(end_date=now + timedelta(hours=4)),
        delta=0.2,
        threshold=0.1,
        strong_moves_count=3,
        now=now,
    )

    assert flags == [LOW_VOLUME, ENDING_SOON, SHARP_MOVE]
    assert VERY_VOLATILE not in flags


def test_risk_flags_detects_missing_data() -> None:
    assert MISSING_DATA in market_risk_flags(_market(probability=None, end_date=None))


def test_count_strong_snapshot_moves() -> None:
    snapshots = [
        MarketSnapshot(market_id="1", question="q", yes_probability=0.1),
        MarketSnapshot(market_id="1", question="q", yes_probability=0.25),
        MarketSnapshot(market_id="1", question="q", yes_probability=0.27),
        MarketSnapshot(market_id="1", question="q", yes_probability=0.4),
    ]
    for index, snapshot in enumerate(snapshots):
        snapshot.created_at = datetime(2026, 5, 14, index, tzinfo=timezone.utc)

    assert count_strong_snapshot_moves(snapshots, 0.1) == 2
