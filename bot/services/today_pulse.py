from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from bot.database.models import MarketSnapshot
from bot.services.market_health import MarketHealth, calculate_market_health
from bot.services.polymarket_client import Market
from bot.services.pulse_score import PulseScore, calculate_pulse_score
from bot.services.risk_flags import market_risk_flags
from bot.utils.formatting import format_compact_usd, format_percentage_points, format_time_until
from bot.utils.i18n import normalize_language


@dataclass(frozen=True, slots=True)
class TodayPulseItem:
    market: Market
    delta: float | None
    pulse_score: PulseScore
    market_health: MarketHealth
    risk_flags: list[str]
    why_it_matters: str


def deduplicate_markets(markets: Sequence[Market]) -> list[Market]:
    seen: set[str] = set()
    result: list[Market] = []
    for market in markets:
        if market.id in seen:
            continue
        seen.add(market.id)
        result.append(market)
    return result


def explain_why_it_matters(
    market: Market,
    pulse_score: PulseScore,
    market_health: MarketHealth,
    delta: float | None = None,
    language: str | None = None,
) -> str:
    normalized = normalize_language(language)
    reasons: list[str] = []

    if pulse_score.value >= 70:
        reasons.append("strong signal" if normalized == "en" else "сильный сигнал")
    elif pulse_score.value >= 40:
        reasons.append("worth watching" if normalized == "en" else "стоит наблюдать")

    if market.volume is not None and market.volume >= 100_000:
        reasons.append(
            f"high activity ({format_compact_usd(market.volume, normalized)})"
            if normalized == "en"
            else f"высокая активность ({format_compact_usd(market.volume, normalized)})"
        )
    if delta is not None and abs(delta) >= 0.05:
        reasons.append(
            f"recent movement {format_percentage_points(delta, normalized)}"
            if normalized == "en"
            else f"движение {format_percentage_points(delta, normalized)}"
        )
    if market.end_date is not None:
        reasons.append(
            f"time left: {format_time_until(market.end_date, language=normalized)}"
            if normalized == "en"
            else f"до завершения: {format_time_until(market.end_date, language=normalized)}"
        )
    if market_health.value >= 70:
        reasons.append("healthy public data" if normalized == "en" else "хорошие публичные данные")

    if not reasons:
        return (
            "Useful discovery candidate based on current public market data."
            if normalized == "en"
            else "Полезный кандидат для наблюдения по текущим публичным данным рынка."
        )

    if normalized == "en":
        return "High activity, " + ", ".join(reasons[:3]) + "."
    return "Интересно: " + ", ".join(reasons[:3]) + "."


def build_today_pulse_items(
    markets: Sequence[Market],
    latest_snapshots: Mapping[str, MarketSnapshot] | None = None,
    threshold: float = 0.10,
    limit: int = 5,
    language: str | None = None,
) -> list[TodayPulseItem]:
    snapshots = latest_snapshots or {}
    complete = [
        market
        for market in deduplicate_markets(markets)
        if market.yes_probability is not None
        and market.volume is not None
        and market.end_date is not None
    ]
    candidates = complete if len(complete) >= min(limit, 3) else deduplicate_markets(markets)

    items: list[TodayPulseItem] = []
    for market in candidates:
        snapshot = snapshots.get(market.id)
        delta = None
        if (
            snapshot is not None
            and snapshot.yes_probability is not None
            and market.yes_probability is not None
        ):
            delta = market.yes_probability - snapshot.yes_probability
        pulse_score = calculate_pulse_score(market, delta=delta)
        market_health = calculate_market_health(market)
        risk_flags = market_risk_flags(market, delta=delta, threshold=threshold)
        items.append(
            TodayPulseItem(
                market=market,
                delta=delta,
                pulse_score=pulse_score,
                market_health=market_health,
                risk_flags=risk_flags,
                why_it_matters=explain_why_it_matters(
                    market,
                    pulse_score,
                    market_health,
                    delta=delta,
                    language=language,
                ),
            )
        )

    return sorted(
        items,
        key=lambda item: (
            item.pulse_score.value,
            item.market.volume or 0,
            abs(item.delta or 0),
            item.market_health.value,
        ),
        reverse=True,
    )[:limit]
