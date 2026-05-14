from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from bot.database.models import MarketSnapshot
from bot.services.polymarket_client import Market

LOW_VOLUME = "⚠️ Low volume"
MISSING_DATA = "⚠️ Missing data"
ENDING_SOON = "⚠️ Ending soon"
SHARP_MOVE = "⚠️ Sharp move"
VERY_VOLATILE = "⚠️ Very volatile"


def count_strong_snapshot_moves(
    snapshots: Iterable[MarketSnapshot],
    threshold: float,
) -> int:
    ordered = sorted(snapshots, key=lambda item: item.created_at)
    count = 0
    previous: float | None = None
    for snapshot in ordered:
        current = snapshot.yes_probability
        if previous is not None and current is not None and abs(current - previous) >= threshold:
            count += 1
        if current is not None:
            previous = current
    return count


def market_risk_flags(
    market: Market,
    delta: float | None = None,
    threshold: float = 0.10,
    strong_moves_count: int = 0,
    now: datetime | None = None,
) -> list[str]:
    flags: list[str] = []
    current = now or datetime.now(timezone.utc)

    if market.volume is not None and market.volume < 10_000:
        flags.append(LOW_VOLUME)
    if market.yes_probability is None or market.end_date is None:
        flags.append(MISSING_DATA)
    if market.end_date is not None:
        end_date = market.end_date
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)
        if (end_date - current).total_seconds() < 24 * 60 * 60:
            flags.append(ENDING_SOON)
    if delta is not None and abs(delta) >= threshold:
        flags.append(SHARP_MOVE)
    if strong_moves_count > 2:
        flags.append(VERY_VOLATILE)

    return flags[:3]
