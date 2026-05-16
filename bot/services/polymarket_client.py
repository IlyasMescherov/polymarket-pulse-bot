from __future__ import annotations

import json
import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class PolymarketAPIError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class Market:
    id: str
    question: str
    slug: str | None
    yes_probability: float | None
    volume: float | None
    end_date: datetime | None
    url: str
    raw: Mapping[str, Any]


def _json_array(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return []
        try:
            loaded = json.loads(value)
        except json.JSONDecodeError:
            return []
        return loaded if isinstance(loaded, list) else []
    return []


def _float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        try:
            return datetime.fromisoformat(f"{value}T00:00:00+00:00")
        except ValueError:
            return None


def _probability_from_outcomes(raw: Mapping[str, Any]) -> float | None:
    outcomes = _json_array(raw.get("outcomes"))
    prices = _json_array(raw.get("outcomePrices"))
    if not prices:
        return None

    index = 0
    for candidate_index, outcome in enumerate(outcomes):
        if isinstance(outcome, str) and outcome.lower() == "yes":
            index = candidate_index
            break

    if index >= len(prices):
        return None

    probability = _float(prices[index])
    if probability is None or probability < 0 or probability > 1:
        return None
    return probability


def parse_market(raw: Mapping[str, Any]) -> Market | None:
    market_id = str(raw.get("id") or "").strip()
    question = str(raw.get("question") or raw.get("title") or raw.get("name") or "").strip()
    if not market_id or not question:
        return None

    slug = str(raw.get("slug") or "").strip() or None
    url = f"https://polymarket.com/market/{slug}" if slug else "https://polymarket.com"
    volume = _float(raw.get("volumeNum")) or _float(raw.get("volume"))
    end_date = _datetime(raw.get("endDate")) or _datetime(raw.get("endDateIso"))

    return Market(
        id=market_id,
        question=question,
        slug=slug,
        yes_probability=_probability_from_outcomes(raw),
        volume=volume,
        end_date=end_date,
        url=url,
        raw=raw,
    )


class PolymarketClient:
    def __init__(
        self,
        base_url: str,
        timeout: float = 15.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=httpx.Timeout(timeout),
            headers={"User-Agent": "PulseMarketBot/0.1"},
        )
        self._event_cache: dict[str, list[Mapping[str, Any]]] = {}

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def _get_markets(
        self,
        params: Mapping[str, Any],
        *,
        enrich_outcomes: bool = True,
    ) -> list[Market]:
        try:
            response = await self._client.get("/markets", params=params)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise PolymarketAPIError("Could not load Polymarket markets") from exc

        if not isinstance(payload, list):
            logger.warning("Unexpected Polymarket response: %s", type(payload).__name__)
            return []

        markets = [market for item in payload if (market := parse_market(item))]
        if enrich_outcomes:
            markets = await self._enrich_grouped_outcomes(markets)
        return markets

    async def _get_payload(self, path: str, params: Mapping[str, Any] | None = None) -> Any:
        response = await self._client.get(path, params=params or {})
        response.raise_for_status()
        return response.json()

    def _markets_from_payload(self, payload: Any) -> list[Market]:
        raw_items: list[Any] = []
        if isinstance(payload, list):
            raw_items = payload
        elif isinstance(payload, dict):
            for key in ("markets", "data", "results", "items"):
                value = payload.get(key)
                if isinstance(value, list):
                    raw_items.extend(value)
            events = payload.get("events")
            if isinstance(events, list):
                for event in events:
                    if isinstance(event, dict):
                        markets = event.get("markets")
                        if isinstance(markets, list):
                            raw_items.extend(markets)

        markets: list[Market] = []
        for item in raw_items:
            if not isinstance(item, Mapping):
                continue
            if market := parse_market(item):
                markets.append(market)
            else:
                nested = item.get("market") or item.get("markets")
                if isinstance(nested, Mapping) and (market := parse_market(nested)):
                    markets.append(market)
        return markets

    async def fetch_markets(
        self,
        limit: int = 100,
        order: str = "volume24hr",
        ascending: bool = False,
    ) -> list[Market]:
        return await self._get_markets(
            {
                "limit": limit,
                "active": "true",
                "closed": "false",
                "order": order,
                "ascending": str(ascending).lower(),
            }
        )

    async def public_search(self, query: str, limit: int = 5) -> list[Market]:
        if not query.strip():
            return []
        attempts = (
            ("/public-search", {"q": query, "limit": limit}),
            ("/public-search", {"query": query, "limit": limit}),
            ("/search", {"q": query, "limit": limit}),
            ("/search", {"query": query, "limit": limit}),
        )
        for path, params in attempts:
            try:
                payload = await self._get_payload(path, params)
            except (httpx.HTTPError, ValueError):
                continue
            markets = self._markets_from_payload(payload)
            if markets:
                return (await self._enrich_grouped_outcomes(markets[:limit]))[:limit]
        return []

    async def get_tags(self) -> list[Mapping[str, Any]]:
        try:
            payload = await self._get_payload("/tags")
        except (httpx.HTTPError, ValueError):
            logger.info("Polymarket tags endpoint unavailable")
            return []
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, Mapping)]
        if isinstance(payload, dict) and isinstance(payload.get("tags"), list):
            return [item for item in payload["tags"] if isinstance(item, Mapping)]
        return []

    async def get_series(self) -> list[Mapping[str, Any]]:
        try:
            payload = await self._get_payload("/series")
        except (httpx.HTTPError, ValueError):
            logger.info("Polymarket series endpoint unavailable")
            return []
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, Mapping)]
        if isinstance(payload, dict) and isinstance(payload.get("series"), list):
            return [item for item in payload["series"] if isinstance(item, Mapping)]
        return []

    async def get_sports_markets(self, limit: int = 5) -> list[Market]:
        try:
            payload = await self._get_payload("/sports", {"limit": limit})
        except (httpx.HTTPError, ValueError):
            payload = None
        markets = self._markets_from_payload(payload) if payload is not None else []
        if markets:
            return (await self._enrich_grouped_outcomes(markets[:limit]))[:limit]
        return await self._get_markets(
            {
                "limit": limit,
                "active": "true",
                "closed": "false",
                "category": "Sports",
            }
        )

    async def find_market_by_id(self, market_id: str) -> Market | None:
        direct_matches = await self._get_markets(
            {
                "id": market_id,
                "limit": 1,
                "active": "true",
                "closed": "false",
            }
        )
        for market in direct_matches:
            if market.id == market_id:
                return market

        markets = await self.fetch_markets(limit=250)
        for market in markets:
            if market.id == market_id:
                return market
        return None

    async def fetch_hot_markets(self, limit: int = 5) -> list[Market]:
        return await self._get_markets(
            {
                "limit": limit,
                "active": "true",
                "closed": "false",
                "order": "volume24hr",
                "ascending": "false",
            }
        )

    async def fetch_new_markets(self, limit: int = 5) -> list[Market]:
        return await self._get_markets(
            {
                "limit": limit,
                "active": "true",
                "closed": "false",
                "order": "createdAt",
                "ascending": "false",
            }
        )

    async def fetch_snapshot_markets(self, limit: int = 50) -> list[Market]:
        markets = await self._get_markets(
            {
                "limit": limit,
                "active": "true",
                "closed": "false",
                "order": "volume24hr",
                "ascending": "false",
            },
            enrich_outcomes=False,
        )
        return [market for market in markets if market.yes_probability is not None]

    async def _enrich_grouped_outcomes(self, markets: list[Market], max_events: int = 8) -> list[Market]:
        """Attach event sibling markets when Gamma exposes grouped outcome events."""

        event_slugs: list[str] = []
        for market in markets:
            slug = _event_slug(market.raw)
            if slug and slug not in event_slugs:
                event_slugs.append(slug)
            if len(event_slugs) >= max_events:
                break

        if not event_slugs:
            return markets

        for slug in event_slugs:
            if slug not in self._event_cache:
                self._event_cache[slug] = await self._fetch_event_markets(slug)

        enriched: list[Market] = []
        for market in markets:
            slug = _event_slug(market.raw)
            event_markets = self._event_cache.get(slug or "", [])
            if not event_markets:
                enriched.append(market)
                continue
            raw = dict(market.raw)
            raw["eventSlug"] = slug
            raw["eventTitle"] = _event_title(raw)
            raw["eventMarkets"] = list(event_markets)
            enriched.append(
                Market(
                    id=market.id,
                    question=market.question,
                    slug=market.slug,
                    yes_probability=market.yes_probability,
                    volume=market.volume,
                    end_date=market.end_date,
                    url=market.url,
                    raw=raw,
                )
            )
        return enriched

    async def _fetch_event_markets(self, slug: str) -> list[Mapping[str, Any]]:
        try:
            payload = await self._get_payload("/events", {"slug": slug, "limit": 1})
        except (httpx.HTTPError, ValueError):
            logger.debug("Could not load Gamma event markets for slug=%s", slug)
            return []

        event: Mapping[str, Any] | None = None
        if isinstance(payload, list) and payload and isinstance(payload[0], Mapping):
            event = payload[0]
        elif isinstance(payload, Mapping):
            event = payload
        if event is None:
            return []
        markets = event.get("markets")
        if not isinstance(markets, list):
            return []
        return [market for market in markets if isinstance(market, Mapping)]


def _event_slug(raw: Mapping[str, Any]) -> str | None:
    direct = str(raw.get("eventSlug") or "").strip()
    if direct:
        return direct
    events = raw.get("events")
    if isinstance(events, list) and events:
        first = events[0]
        if isinstance(first, Mapping):
            slug = str(first.get("slug") or "").strip()
            return slug or None
    return None


def _event_title(raw: Mapping[str, Any]) -> str | None:
    direct = str(raw.get("eventTitle") or "").strip()
    if direct:
        return direct
    events = raw.get("events")
    if isinstance(events, list) and events:
        first = events[0]
        if isinstance(first, Mapping):
            title = str(first.get("title") or "").strip()
            return title or None
    return None
