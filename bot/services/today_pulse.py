from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from bot.database.models import MarketSnapshot
from bot.services.market_health import MarketHealth, calculate_market_health
from bot.services.polymarket_client import Market
from bot.services.pulse_score import PulseScore, calculate_pulse_score
from bot.services.risk_flags import market_risk_flags
from bot.utils.i18n import normalize_language


def _title_category_reason(market: Market, language: str) -> str:
    title = market.question.lower()
    if any(word in title for word in ("bitcoin", "btc", "ethereum", "crypto", "binance")):
        return (
            "Crypto volatility made this market more visible."
            if language == "en"
            else "Активность усилилась после движения крипторынка."
        )
    if any(word in title for word in ("iran", "israel", "trump", "election", "president", "war", "diplomacy")):
        return (
            "Political headlines made this market more visible."
            if language == "en"
            else "Политическая повестка сделала рынок заметнее."
        )
    if any(word in title for word in ("nba", "nfl", "ufc", "soccer", "football", "tennis", "match", "playoff")):
        return (
            "Event timing made this market more visible."
            if language == "en"
            else "Рынок оживился перед спортивным событием."
        )
    if any(word in title for word in ("openai", "nvidia", "anthropic", " ai ")):
        return (
            "AI news flow made this topic more visible today."
            if language == "en"
            else "Внимание к AI-теме усилилось."
        )
    return (
        "The topic became more visible in today’s market read."
        if language == "en"
        else "Тема стала заметнее в сегодняшнем чтении рынка."
    )


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
    if delta is not None and abs(delta) >= 0.05:
        return (
            "Probability moved today, so the market deserves a closer read."
            if normalized == "en"
            else "Вероятность сегодня изменилась, поэтому рынок заслуживает разбора."
        )

    if market.volume is not None and market.volume >= 100_000:
        return _title_category_reason(market, normalized)

    if pulse_score.value >= 70:
        return (
            "Pulse Score makes this one of today’s clearer stories."
            if normalized == "en"
            else "Pulse Score выделяет этот рынок среди понятных историй дня."
        )

    if market_health.value >= 70:
        return (
            "The market has enough public data to read quickly."
            if normalized == "en"
            else "По рынку достаточно публичных данных, чтобы быстро понять ситуацию."
        )

    return (
        "The story is still forming, but attention is present."
        if normalized == "en"
        else "История ещё формируется, но интерес уже есть."
    )


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
