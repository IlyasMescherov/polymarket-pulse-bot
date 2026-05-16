from __future__ import annotations

from datetime import datetime, timedelta, timezone

from bot.database.models import MarketSnapshot
from bot.services.market_regime_engine import classify_market_regime


def _snapshot(probability: float, volume: float, hours_ago: int = 12) -> MarketSnapshot:
    snapshot = MarketSnapshot(
        market_id="m1",
        question="Will Bitcoin hit $150k by December 31, 2026?",
        yes_probability=probability,
        volume=volume,
    )
    snapshot.created_at = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    return snapshot


def _market(**overrides: object) -> dict:
    base = {
        "title": "Will Bitcoin hit $150k by December 31, 2026?",
        "probability": 0.42,
        "volume": 120_000,
        "end_date": datetime.now(timezone.utc) + timedelta(days=20),
    }
    base.update(overrides)
    return base


def test_activity_up_probability_flat_gives_short_term_attention() -> None:
    history = [_snapshot(0.415, 60_000)]
    regime = classify_market_regime(_market(probability=0.42, volume=120_000), history, lang="en")

    assert regime.key == "short_term_attention"
    assert regime.label == "Short-term attention"


def test_probability_moved_weak_volume_gives_weak_confirmation() -> None:
    history = [_snapshot(0.31, 8_000)]
    regime = classify_market_regime(_market(probability=0.38, volume=12_000), history, lang="en")

    assert regime.key == "weak_confirmation"
    assert regime.label == "Weak confirmation"


def test_ending_soon_activity_gives_near_resolution_ru() -> None:
    history = [_snapshot(0.41, 60_000)]
    market = _market(
        probability=0.42,
        volume=110_000,
        end_date=datetime.now(timezone.utc) + timedelta(hours=6),
    )
    regime = classify_market_regime(market, history, lang="ru")

    assert regime.key == "near_resolution"
    assert regime.label == "Перед завершением"


def test_related_market_movement_affects_regime() -> None:
    history = [_snapshot(0.40, 100_000)]
    regime = classify_market_regime(
        _market(probability=0.44, volume=160_000),
        history,
        related_count=3,
        lang="en",
    )

    assert regime.key in {"news_reaction", "more_confident"}
    assert regime.reason
