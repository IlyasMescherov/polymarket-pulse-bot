from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from bot.database.models import MarketSnapshot
from bot.services.market_health import MarketHealth, calculate_market_health
from bot.services.polymarket_client import Market
from bot.services.pulse_score import PulseScore, calculate_pulse_score
from bot.services.risk_flags import market_risk_flags
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
    if delta is not None and abs(delta) >= 0.05:
        return (
            "Attention is rising because probability moved today."
            if normalized == "en"
            else "Внимание растёт, потому что вероятность сегодня изменилась."
        )

    if market.volume is not None and market.volume >= 100_000:
        return (
            "People are watching this because activity increased."
            if normalized == "en"
            else "За этим следят, потому что активность выросла."
        )

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
        "People are paying attention, but the story is still early."
        if normalized == "en"
        else "Интерес есть, но история ещё только формируется."
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
