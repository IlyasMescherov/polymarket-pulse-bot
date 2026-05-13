from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.repositories import get_latest_snapshots, save_market_snapshots
from bot.services.polymarket_client import Market, PolymarketClient


@dataclass(frozen=True, slots=True)
class MarketMovement:
    market: Market
    old_probability: float
    new_probability: float
    delta: float


def probability_delta(old_probability: float | None, new_probability: float | None) -> float | None:
    if old_probability is None or new_probability is None:
        return None
    return new_probability - old_probability


def is_sharp_move(
    old_probability: float | None,
    new_probability: float | None,
    threshold: float,
) -> bool:
    delta = probability_delta(old_probability, new_probability)
    return delta is not None and abs(delta) >= threshold


class MarketAnalyzer:
    def __init__(self, client: PolymarketClient, movement_threshold: float = 0.10) -> None:
        self._client = client
        self._movement_threshold = movement_threshold

    async def get_hot_markets(self, limit: int = 5) -> list[Market]:
        return await self._client.fetch_hot_markets(limit=limit)

    async def get_new_markets(self, limit: int = 5) -> list[Market]:
        return await self._client.fetch_new_markets(limit=limit)

    async def detect_movements(
        self,
        session: AsyncSession,
        limit: int = 50,
    ) -> list[MarketMovement]:
        markets = await self._client.fetch_snapshot_markets(limit=limit)
        latest = await get_latest_snapshots(session, [market.id for market in markets])

        movements: list[MarketMovement] = []
        for market in markets:
            snapshot = latest.get(market.id)
            if snapshot is None:
                continue

            delta = probability_delta(snapshot.yes_probability, market.yes_probability)
            if delta is None or abs(delta) < self._movement_threshold:
                continue

            movements.append(
                MarketMovement(
                    market=market,
                    old_probability=snapshot.yes_probability,
                    new_probability=market.yes_probability,
                    delta=delta,
                )
            )

        await save_market_snapshots(session, markets)
        await session.commit()
        return sorted(movements, key=lambda item: abs(item.delta), reverse=True)

