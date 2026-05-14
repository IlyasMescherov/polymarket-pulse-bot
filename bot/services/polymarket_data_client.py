from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import httpx

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class DataTrade:
    market_id: str
    market_title: str
    wallet_address: str | None
    amount_usd: float | None
    price: float | None
    size: float | None
    outcome: str | None
    timestamp: datetime | None
    raw: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class LeaderboardTrader:
    wallet_address: str | None
    display_name: str | None
    volume: float | None
    trades_count: int | None
    rank: int | None
    raw: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class DataPosition:
    wallet_address: str | None
    market_id: str
    market_title: str
    size: float | None
    current_value: float | None
    raw: Mapping[str, Any]


def _float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _datetime(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        timestamp = float(value)
        if timestamp > 10_000_000_000:
            timestamp /= 1000
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)
    if not isinstance(value, str):
        return None
    normalized = value.strip().replace("Z", "+00:00")
    if not normalized:
        return None
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def _text(raw: Mapping[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = raw.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return None


def _nested_text(raw: Mapping[str, Any], key: str, *nested_keys: str) -> str | None:
    value = raw.get(key)
    if isinstance(value, Mapping):
        return _text(value, *nested_keys)
    return None


def _items(payload: Any, keys: tuple[str, ...]) -> list[Mapping[str, Any]]:
    raw_items: list[Any] = []
    if isinstance(payload, list):
        raw_items = payload
    elif isinstance(payload, Mapping):
        for key in keys:
            value = payload.get(key)
            if isinstance(value, list):
                raw_items.extend(value)
    return [item for item in raw_items if isinstance(item, Mapping)]


def _amount_usd(raw: Mapping[str, Any]) -> float | None:
    for key in (
        "amountUsd",
        "amountUSD",
        "usdAmount",
        "notional",
        "value",
        "cashAmount",
        "volume",
        "amount",
    ):
        value = _float(raw.get(key))
        if value is not None:
            return value
    size = _float(raw.get("size") or raw.get("shares"))
    price = _float(raw.get("price"))
    if size is not None and price is not None:
        return abs(size * price)
    return None


def parse_data_trade(raw: Mapping[str, Any]) -> DataTrade | None:
    market_title = (
        _text(raw, "marketTitle", "title", "question", "marketQuestion")
        or _nested_text(raw, "market", "question", "title", "name")
        or "Unknown market"
    )
    market_id = (
        _text(raw, "marketId", "conditionId", "market", "marketSlug", "asset")
        or _nested_text(raw, "market", "id", "conditionId", "slug")
        or market_title[:64]
    )
    if not market_id:
        return None
    return DataTrade(
        market_id=market_id,
        market_title=market_title,
        wallet_address=_text(raw, "wallet", "user", "proxyWallet", "trader", "maker"),
        amount_usd=_amount_usd(raw),
        price=_float(raw.get("price")),
        size=_float(raw.get("size") or raw.get("shares")),
        outcome=_text(raw, "outcome", "outcomeName", "side"),
        timestamp=_datetime(raw.get("timestamp") or raw.get("createdAt") or raw.get("time")),
        raw=raw,
    )


def parse_leaderboard_trader(raw: Mapping[str, Any]) -> LeaderboardTrader:
    return LeaderboardTrader(
        wallet_address=_text(raw, "wallet", "address", "proxyWallet", "user"),
        display_name=_text(raw, "name", "username", "displayName", "profileName"),
        volume=_float(raw.get("volume") or raw.get("vol") or raw.get("totalVolume")),
        trades_count=_int(raw.get("trades") or raw.get("tradesCount") or raw.get("count")),
        rank=_int(raw.get("rank") or raw.get("position")),
        raw=raw,
    )


def parse_data_position(raw: Mapping[str, Any]) -> DataPosition | None:
    market_title = (
        _text(raw, "marketTitle", "title", "question")
        or _nested_text(raw, "market", "question", "title", "name")
        or "Unknown market"
    )
    market_id = (
        _text(raw, "marketId", "conditionId", "market")
        or _nested_text(raw, "market", "id", "conditionId", "slug")
        or market_title[:64]
    )
    if not market_id:
        return None
    return DataPosition(
        wallet_address=_text(raw, "wallet", "address", "proxyWallet", "user"),
        market_id=market_id,
        market_title=market_title,
        size=_float(raw.get("size") or raw.get("shares")),
        current_value=_float(raw.get("currentValue") or raw.get("value") or raw.get("cashValue")),
        raw=raw,
    )


class PolymarketDataClient:
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

    async def _get_payload(self, path: str, params: Mapping[str, Any]) -> Any | None:
        try:
            response = await self._client.get(path, params=params)
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.info("Polymarket Data API unavailable for %s: %s", path, exc)
            return None

    async def get_trades(
        self,
        limit: int = 50,
        user: str | None = None,
        market: str | None = None,
    ) -> list[DataTrade]:
        params: dict[str, Any] = {"limit": limit}
        if user:
            params["user"] = user
        if market:
            params["market"] = market
        payload = await self._get_payload("/trades", params)
        if payload is None:
            return []
        trades = [
            trade
            for item in _items(payload, ("data", "trades", "items", "results"))
            if (trade := parse_data_trade(item))
        ]
        return trades[:limit]

    async def get_leaderboard(self, limit: int = 10) -> list[LeaderboardTrader]:
        attempts = (
            ("/v1/leaderboard", {"limit": limit, "timePeriod": "DAY", "orderBy": "VOL"}),
            ("/leaderboard", {"limit": limit}),
        )
        for path, params in attempts:
            payload = await self._get_payload(path, params)
            if payload is None:
                continue
            traders = [
                parse_leaderboard_trader(item)
                for item in _items(payload, ("data", "leaderboard", "items", "results"))
            ]
            if traders:
                return traders[:limit]
        return []

    async def get_positions(self, wallet_address: str, limit: int = 50) -> list[DataPosition]:
        attempts = (
            ("/positions", {"user": wallet_address, "limit": limit}),
            ("/positions", {"address": wallet_address, "limit": limit}),
        )
        for path, params in attempts:
            payload = await self._get_payload(path, params)
            if payload is None:
                continue
            positions = [
                position
                for item in _items(payload, ("data", "positions", "items", "results"))
                if (position := parse_data_position(item))
            ]
            if positions:
                return positions[:limit]
        return []
