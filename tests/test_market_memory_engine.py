from __future__ import annotations

from datetime import datetime, timedelta, timezone

from bot.database.models import MarketSnapshot
from bot.services.market_memory_engine import (
    compare_current_to_previous,
    detect_memory_pattern,
    generate_memory_summary,
)


def _snapshot(
    probability: float,
    volume: float,
    hours_ago: int,
    market_id: str = "m1",
) -> MarketSnapshot:
    snapshot = MarketSnapshot(
        market_id=market_id,
        question="Will Bitcoin hit $150k by December 31, 2026?",
        yes_probability=probability,
        volume=volume,
    )
    snapshot.created_at = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    return snapshot


def _market(**overrides: object) -> dict:
    base = {
        "id": "m1",
        "title": "Will Bitcoin hit $150k by December 31, 2026?",
        "probability": 0.42,
        "volume": 180_000,
        "end_date": datetime.now(timezone.utc) + timedelta(days=12),
    }
    base.update(overrides)
    return base


def test_market_memory_works_with_no_history() -> None:
    memory = generate_memory_summary(_market(), [], lang="en")

    assert not memory.has_history
    assert memory.summary == "Not enough history for comparison yet."
    assert memory.pattern
    assert memory.changed_since_last_seen


def test_market_memory_detects_activity_holding_with_flat_probability() -> None:
    history = [
        _snapshot(0.40, 100_000, 30),
        _snapshot(0.415, 140_000, 12),
    ]

    memory = compare_current_to_previous(
        _market(probability=0.42, volume=180_000),
        history,
        lang="en",
    )

    assert memory.has_history
    assert "Activity is holding" in memory.summary
    assert memory.volume_change_24h == 40_000
    assert memory.probability_change_24h == 0.005


def test_market_memory_detects_near_resolution_pattern_ru() -> None:
    history = [_snapshot(0.41, 100_000, 8)]
    market = _market(
        probability=0.42,
        volume=140_000,
        end_date=datetime.now(timezone.utc) + timedelta(hours=8),
    )

    assert detect_memory_pattern(market, history, lang="ru") == "Рынок заметен перед завершением"
