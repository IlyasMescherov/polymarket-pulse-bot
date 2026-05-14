from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.repositories import get_latest_snapshots, save_market_snapshots
from bot.services.polymarket_client import Market, PolymarketClient

CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "politics": ("trump", "election", "president", "senate", "congress", "biden"),
    "crypto": ("bitcoin", "ethereum", "solana", "crypto", "btc", "eth", "xrp"),
    "ai_tech": ("ai", "openai", "nvidia", "tesla", "apple", "google", "microsoft"),
    "sports": ("nba", "nfl", "ufc", "soccer", "football", "tennis"),
    "economy": ("fed", "inflation", "rates", "recession", "cpi", "jobs"),
}

CATEGORY_LABELS: dict[str, str] = {
    "politics": "Politics",
    "crypto": "Crypto",
    "ai_tech": "AI / Tech",
    "sports": "Sports",
    "economy": "Economy",
}


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


def _category_text(market: Market) -> str:
    raw_category = market.raw.get("category")
    if isinstance(raw_category, dict):
        category = " ".join(str(value) for value in raw_category.values())
    else:
        category = str(raw_category or "")
    raw_tags = market.raw.get("tags") or market.raw.get("tag")
    if isinstance(raw_tags, list):
        tags = " ".join(
            str(value.get("label") or value.get("name") or value)
            if isinstance(value, dict)
            else str(value)
            for value in raw_tags
        )
    else:
        tags = str(raw_tags or "")
    return f"{market.question} {category} {tags}".lower()


def market_matches_topics(market: Market, topics: list[str]) -> bool:
    if not topics:
        return True
    text = _category_text(market)
    return any(topic.lower() in text for topic in topics)


def filter_markets_by_query(markets: list[Market], query: str) -> list[Market]:
    tokens = [token for token in query.lower().split() if token]
    if not tokens:
        return []
    return [
        market
        for market in markets
        if all(token in _category_text(market) for token in tokens)
    ]


def filter_markets_by_category(markets: list[Market], category: str) -> list[Market]:
    keywords = CATEGORY_KEYWORDS.get(category, ())
    if not keywords:
        return []
    return [
        market
        for market in markets
        if any(keyword in _category_text(market) for keyword in keywords)
    ]


class MarketAnalyzer:
    def __init__(self, client: PolymarketClient, movement_threshold: float = 0.10) -> None:
        self._client = client
        self._movement_threshold = movement_threshold

    async def get_hot_markets(self, limit: int = 5) -> list[Market]:
        return await self._client.fetch_hot_markets(limit=limit)

    async def get_new_markets(self, limit: int = 5) -> list[Market]:
        return await self._client.fetch_new_markets(limit=limit)

    async def search_markets(self, query: str, limit: int = 5) -> list[Market]:
        markets = await self._client.fetch_markets(limit=150)
        return filter_markets_by_query(markets, query)[:limit]

    async def get_category_markets(self, category: str, limit: int = 5) -> list[Market]:
        markets = await self._client.fetch_markets(limit=150)
        return filter_markets_by_category(markets, category)[:limit]

    async def find_market_by_id(self, market_id: str) -> Market | None:
        return await self._client.find_market_by_id(market_id)

    async def detect_movements(
        self,
        session: AsyncSession,
        limit: int = 50,
        threshold: float | None = None,
    ) -> list[MarketMovement]:
        markets = await self._client.fetch_snapshot_markets(limit=limit)
        latest = await get_latest_snapshots(session, [market.id for market in markets])
        movement_threshold = threshold or self._movement_threshold

        movements: list[MarketMovement] = []
        for market in markets:
            snapshot = latest.get(market.id)
            if snapshot is None:
                continue

            delta = probability_delta(snapshot.yes_probability, market.yes_probability)
            if delta is None or abs(delta) < movement_threshold:
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
