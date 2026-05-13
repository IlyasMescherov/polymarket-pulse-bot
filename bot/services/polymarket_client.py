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
    question = str(raw.get("question") or "").strip()
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

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def _get_markets(self, params: Mapping[str, Any]) -> list[Market]:
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
        return markets

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
            }
        )
        return [market for market in markets if market.yes_probability is not None]

