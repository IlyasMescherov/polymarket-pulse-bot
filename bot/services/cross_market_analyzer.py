from __future__ import annotations

from collections import defaultdict
from typing import Any, Mapping

from bot.services.ai_prompts import validate_ai_output

_TOPIC_KEYWORDS: tuple[tuple[str, tuple[str, ...], str], ...] = (
    ("Iran / US diplomacy", ("iran", "us", "u.s.", "diplomacy", "nuclear", "israel"), "politics"),
    ("Bitcoin volatility", ("bitcoin", "btc", "crypto", "binance"), "crypto"),
    ("AI news cycle", ("openai", "nvidia", "anthropic", "ai"), "ai"),
    ("Sports event window", ("nba", "nfl", "ufc", "match", "playoff", "football", "soccer"), "sports"),
    ("Global macro events", ("fed", "inflation", "rates", "cpi", "recession"), "global"),
)


def _market_title(market: Mapping[str, Any]) -> str:
    return str(market.get("title") or market.get("question") or "")


def _delta(market: Mapping[str, Any]) -> float:
    raw = market.get("probability_delta", market.get("delta", market.get("movement", 0)))
    try:
        value = abs(float(raw or 0))
    except (TypeError, ValueError):
        return 0.0
    return value * 100 if value <= 1 else value


def _topic_for_market(market: Mapping[str, Any]) -> tuple[str, str]:
    text = f"{_market_title(market)} {market.get('description') or ''}".lower()
    for label, keywords, category in _TOPIC_KEYWORDS:
        if any(keyword in text for keyword in keywords):
            return label, category
    category = str(market.get("category") or "global")
    return category.replace("_", " ").title(), category


def _group_interpretation(label: str, markets: list[Mapping[str, Any]]) -> str:
    high_activity = sum(1 for market in markets if float(market.get("volume") or market.get("public_activity") or 0) >= 100_000)
    moved = sum(1 for market in markets if _delta(market) >= 2)
    if moved >= 2 and high_activity >= 2:
        text = (
            f"Several markets around {label} moved together. "
            "That makes the theme more important to review."
        )
    elif high_activity >= 2:
        text = (
            f"Several markets around {label} became busier, but most expectations still look stable."
        )
    else:
        text = (
            f"{label} is visible across related markets, but the read is still early."
        )
    return "The cross-market read was filtered." if validate_ai_output(text) else text


def group_markets_by_narrative(markets: list[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    categories: dict[str, str] = {}
    for market in markets:
        label, category = _topic_for_market(market)
        grouped[label].append(market)
        categories[label] = category

    results: list[dict] = []
    for label, items in grouped.items():
        if len(items) < 2:
            continue
        group = {
            "narrative": label,
            "category": categories[label],
            "markets": items,
            "group_interpretation": _group_interpretation(label, items),
        }
        divergence = detect_divergence(group)
        if divergence:
            group["divergence"] = divergence
        results.append(group)
    return sorted(results, key=lambda item: len(item["markets"]), reverse=True)


def detect_divergence(group: dict) -> str | None:
    markets = group.get("markets")
    if not isinstance(markets, list) or len(markets) < 2:
        return None
    positive = sum(
        1
        for market in markets
        if float(market.get("probability_delta", market.get("delta", market.get("movement", 0))) or 0) > 0
    )
    negative = sum(
        1
        for market in markets
        if float(market.get("probability_delta", market.get("delta", market.get("movement", 0))) or 0) < 0
    )
    if positive and negative:
        return (
            f"{group.get('narrative', 'This theme')} has mixed market movement. "
            "Shorter-term markets look more reactive than the broader theme."
        )
    return None
