from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from bot.services.polymarket_client import Market


@dataclass(frozen=True, slots=True)
class PulseScore:
    value: int
    label: str


def pulse_score_label(value: int) -> str:
    if value <= 39:
        return "Low signal"
    if value <= 69:
        return "Worth watching"
    return "Strong signal"


def _volume_points(volume: float | None) -> int:
    if volume is None:
        return 3
    if volume >= 500_000:
        return 35
    if volume >= 100_000:
        return 25
    if volume >= 50_000:
        return 18
    if volume >= 10_000:
        return 10
    return 3


def _ending_points(end_date: datetime | None, now: datetime | None = None) -> int:
    if end_date is None:
        return 2
    current = now or datetime.now(timezone.utc)
    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=timezone.utc)
    seconds_left = (end_date - current).total_seconds()
    if seconds_left < 24 * 60 * 60:
        return 12
    if seconds_left < 7 * 24 * 60 * 60:
        return 8
    if seconds_left < 30 * 24 * 60 * 60:
        return 5
    return 2


def calculate_pulse_score(
    market: Market,
    delta: float | None = None,
    now: datetime | None = None,
) -> PulseScore:
    movement_points = min(abs(delta or 0) * 100 * 3, 45)
    volume_points = _volume_points(market.volume)
    ending_points = _ending_points(market.end_date, now=now)
    data_quality_points = (
        10
        if market.yes_probability is not None
        and market.volume is not None
        and market.end_date is not None
        else 5
    )
    value = min(
        100,
        round(
            movement_points
            + volume_points
            + ending_points
            + data_quality_points
        ),
    )
    return PulseScore(value=value, label=pulse_score_label(value))
