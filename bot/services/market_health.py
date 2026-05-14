from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from bot.services.polymarket_client import Market


@dataclass(frozen=True, slots=True)
class MarketHealth:
    value: int
    label: str


def market_health_label(value: int) -> str:
    if value <= 39:
        return "Risky"
    if value <= 69:
        return "Medium"
    return "Healthy"


def _volume_points(volume: float | None) -> int:
    if volume is None:
        return 0
    if volume >= 500_000:
        return 45
    if volume >= 100_000:
        return 35
    if volume >= 50_000:
        return 25
    if volume >= 10_000:
        return 15
    return 5


def _ending_points(end_date: datetime | None, now: datetime | None = None) -> int:
    if end_date is None:
        return 0
    current = now or datetime.now(timezone.utc)
    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=timezone.utc)
    seconds_left = (end_date - current).total_seconds()
    if seconds_left <= 0:
        return 2
    if seconds_left < 24 * 60 * 60:
        return 4
    if seconds_left < 7 * 24 * 60 * 60:
        return 8
    return 10


def _spread_points(spread: float | None) -> int:
    if spread is None:
        return 0
    if spread <= 0.02:
        return 10
    if spread <= 0.05:
        return 6
    return 2


def _depth_points(orderbook_depth: float | None) -> int:
    if orderbook_depth is None:
        return 0
    if orderbook_depth >= 10_000:
        return 5
    if orderbook_depth >= 1_000:
        return 3
    return 1


def calculate_market_health(
    market: Market,
    spread: float | None = None,
    orderbook_depth: float | None = None,
    now: datetime | None = None,
) -> MarketHealth:
    value = (
        _volume_points(market.volume)
        + (15 if market.yes_probability is not None else 0)
        + (15 if market.end_date is not None else 0)
        + _ending_points(market.end_date, now=now)
        + _spread_points(spread)
        + _depth_points(orderbook_depth)
    )
    value = min(100, round(value))
    return MarketHealth(value=value, label=market_health_label(value))
