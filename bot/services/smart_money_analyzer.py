from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime

from bot.services.polymarket_data_client import (
    DataTrade,
    LeaderboardTrader,
    PolymarketDataClient,
)
from bot.utils.formatting import format_compact_usd

WALLET_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")
DEFAULT_LARGE_TRADE_USD = 10_000.0
DEFAULT_ACTIVE_MARKET_MIN_USD = 1000.0


@dataclass(frozen=True, slots=True)
class LargeTradeSignal:
    market_id: str
    market_title: str
    wallet_address: str | None
    amount_usd: float
    timestamp: datetime | None


@dataclass(frozen=True, slots=True)
class TraderScore:
    wallet_address: str | None
    display_name: str | None
    score: int
    label: str
    volume: float | None
    trades_count: int | None
    rank: int | None


@dataclass(frozen=True, slots=True)
class MarketActivity:
    market_id: str
    market_title: str
    amount_usd: float
    trades_count: int
    participant_count: int


def validate_wallet_address(address: str) -> bool:
    return bool(WALLET_RE.fullmatch(address.strip()))


def detect_large_trades(
    trades: list[DataTrade],
    min_usd: float = DEFAULT_LARGE_TRADE_USD,
    limit: int = 5,
) -> list[LargeTradeSignal]:
    signals = [
        LargeTradeSignal(
            market_id=trade.market_id,
            market_title=trade.market_title,
            wallet_address=trade.wallet_address,
            amount_usd=trade.amount_usd,
            timestamp=trade.timestamp,
        )
        for trade in trades
        if trade.amount_usd is not None and trade.amount_usd >= min_usd
    ]
    return sorted(signals, key=lambda item: item.amount_usd, reverse=True)[:limit]


def score_public_trader(trader: LeaderboardTrader) -> TraderScore:
    volume = trader.volume or 0
    trades_count = trader.trades_count or 0
    volume_points = 0
    if volume >= 1_000_000:
        volume_points = 55
    elif volume >= 250_000:
        volume_points = 40
    elif volume >= 50_000:
        volume_points = 25
    elif volume > 0:
        volume_points = 10

    activity_points = 3
    if trades_count >= 100:
        activity_points = 25
    elif trades_count >= 25:
        activity_points = 15
    elif trades_count >= 5:
        activity_points = 8

    data_points = 20 if trader.wallet_address and validate_wallet_address(trader.wallet_address) else 10
    score = min(100, volume_points + activity_points + data_points)
    if score >= 70:
        label = "High public activity"
    elif score >= 40:
        label = "Active public participant"
    else:
        label = "Limited public data"

    return TraderScore(
        wallet_address=trader.wallet_address,
        display_name=trader.display_name,
        score=score,
        label=label,
        volume=trader.volume,
        trades_count=trader.trades_count,
        rank=trader.rank,
    )


def aggregate_market_activity(
    trades: list[DataTrade],
    min_usd: float = DEFAULT_ACTIVE_MARKET_MIN_USD,
    limit: int = 5,
) -> list[MarketActivity]:
    totals: dict[str, float] = defaultdict(float)
    counts: dict[str, int] = defaultdict(int)
    titles: dict[str, str] = {}
    participants: dict[str, set[str]] = defaultdict(set)

    for trade in trades:
        amount = trade.amount_usd or 0
        if amount <= 0:
            continue
        totals[trade.market_id] += amount
        counts[trade.market_id] += 1
        titles[trade.market_id] = trade.market_title
        if trade.wallet_address:
            participants[trade.market_id].add(trade.wallet_address.lower())

    activities = [
        MarketActivity(
            market_id=market_id,
            market_title=titles.get(market_id, "Unknown market"),
            amount_usd=amount,
            trades_count=counts[market_id],
            participant_count=len(participants[market_id]),
        )
        for market_id, amount in totals.items()
        if amount >= min_usd
    ]
    return sorted(
        activities,
        key=lambda item: (item.amount_usd, item.trades_count, item.participant_count),
        reverse=True,
    )[:limit]


def explain_large_trade(signal: LargeTradeSignal, language: str | None = None) -> str:
    if language == "ru":
        return "\n".join(
            [
                "🐋 Всплеск публичной активности",
                "",
                "PulseMarket заметил заметную публичную активность.",
                f"Размер: {format_compact_usd(signal.amount_usd, 'ru')}.",
                "",
                "Почему людям это интересно:",
                "Так можно увидеть, куда смещается внимание рынка.",
                "",
                "Что смотреть:",
                "Вероятность, активность и правила разрешения.",
                "",
                "Для анализа · Без сделок",
            ]
        )

    return "\n".join(
        [
            "🐋 Public activity spike",
            "",
            "PulseMarket noticed visible public activity.",
            f"Size: {format_compact_usd(signal.amount_usd, 'en')}.",
            "",
            "Why people care:",
            "It can show where market attention is moving.",
            "",
            "Watch:",
            "Probability, activity, and resolution rules.",
            "",
            "Research only · No trade execution",
        ]
    )


def explain_market_activity(activity: MarketActivity, language: str | None = None) -> str:
    if language == "ru":
        return "\n".join(
            [
                "📈 Рынок с ростом внимания",
                "",
                activity.market_title,
                "",
                "Почему людям это интересно:",
                "Внимание к этому рынку растёт.",
                "",
                "Публичная активность:",
                format_compact_usd(activity.amount_usd, "ru"),
                "",
                "Для анализа · Без сделок",
            ]
        )

    return "\n".join(
        [
            "📈 Market getting attention",
            "",
            activity.market_title,
            "",
            "Why people care:",
            "Attention is rising around this market.",
            "",
            "Public activity:",
            format_compact_usd(activity.amount_usd, "en"),
            "",
            "Research only · No trade execution",
        ]
    )


class SmartMoneyAnalyzer:
    def __init__(
        self,
        data_client: PolymarketDataClient,
        large_trade_usd: float = DEFAULT_LARGE_TRADE_USD,
        active_market_min_usd: float = DEFAULT_ACTIVE_MARKET_MIN_USD,
    ) -> None:
        self._data_client = data_client
        self._large_trade_usd = large_trade_usd
        self._active_market_min_usd = active_market_min_usd

    async def unusual_activity(self, limit: int = 5) -> list[LargeTradeSignal]:
        trades = await self._data_client.get_trades(limit=100)
        return detect_large_trades(trades, min_usd=self._large_trade_usd, limit=limit)

    async def public_traders(self, limit: int = 5) -> list[TraderScore]:
        traders = await self._data_client.get_leaderboard(limit=limit)
        return [score_public_trader(trader) for trader in traders[:limit]]

    async def active_markets(self, limit: int = 5) -> list[MarketActivity]:
        trades = await self._data_client.get_trades(limit=100)
        return aggregate_market_activity(
            trades,
            min_usd=self._active_market_min_usd,
            limit=limit,
        )
