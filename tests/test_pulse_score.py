from __future__ import annotations

from datetime import datetime, timedelta, timezone

from bot.services.polymarket_client import Market
from bot.services.pulse_score import calculate_pulse_score, pulse_score_label


def _market(volume: float | None, end_date: datetime | None, probability: float | None = 0.63) -> Market:
    return Market(
        id="1",
        question="Will this market be interesting?",
        slug=None,
        yes_probability=probability,
        volume=volume,
        end_date=end_date,
        url="https://polymarket.com",
        raw={},
    )


def test_pulse_score_rewards_movement_volume_and_complete_data() -> None:
    now = datetime(2026, 5, 14, tzinfo=timezone.utc)
    score = calculate_pulse_score(
        _market(600_000, now + timedelta(hours=12)),
        delta=0.12,
        now=now,
    )

    assert score.value == 93
    assert score.label == "Strong signal"


def test_pulse_score_labels() -> None:
    assert pulse_score_label(20) == "Low signal"
    assert pulse_score_label(55) == "Worth watching"
    assert pulse_score_label(80) == "Strong signal"
