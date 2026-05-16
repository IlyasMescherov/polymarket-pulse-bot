from __future__ import annotations

from collections.abc import Iterable

from bot.services.source_adapters.base import ExternalNewsItem, SourceConfig


SOURCE_TYPE_BASE_SCORES: dict[str, float] = {
    "official": 92.0,
    "mainstream": 82.0,
    "news_api": 76.0,
    "rss": 68.0,
    "x": 46.0,
    "telegram": 44.0,
}


def credibility_for_source(source: SourceConfig | ExternalNewsItem | dict) -> float:
    if isinstance(source, dict):
        source_type = str(source.get("source_type") or "rss")
        explicit = source.get("credibility_score")
    else:
        source_type = source.source_type
        explicit = getattr(source, "credibility_score", None)
    try:
        score = float(explicit)
    except (TypeError, ValueError):
        score = SOURCE_TYPE_BASE_SCORES.get(source_type, 60.0)
    return max(0.0, min(100.0, score))


def credibility_band(score: float) -> str:
    if score >= 80:
        return "high"
    if score >= 60:
        return "medium"
    return "low"


def source_mix(events: Iterable[ExternalNewsItem]) -> dict[str, int]:
    mix: dict[str, int] = {}
    for event in events:
        mix[event.source_type] = mix.get(event.source_type, 0) + 1
    return mix


def official_source_present(events: Iterable[ExternalNewsItem]) -> bool:
    return any(event.source_type == "official" for event in events)


def credible_source_count(events: Iterable[ExternalNewsItem], threshold: float = 75.0) -> int:
    return sum(1 for event in events if credibility_for_source(event) >= threshold)


def news_confidence(events: Iterable[ExternalNewsItem]) -> str:
    material = list(events)
    if not material:
        return "low"
    if official_source_present(material):
        return "high"
    if credible_source_count(material) >= 2:
        return "medium"
    return "low"
