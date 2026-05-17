from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from bot.services.source_adapters.base import ExternalNewsItem


STOPWORDS = {
    "about",
    "after",
    "again",
    "against",
    "before",
    "during",
    "event",
    "events",
    "from",
    "have",
    "into",
    "market",
    "markets",
    "over",
    "than",
    "that",
    "this",
    "will",
    "with",
    "would",
    "whether",
    "candidate",
    "candidates",
    "latest",
    "news",
    "official",
    "officials",
    "presidential",
    "public",
    "source",
    "что",
    "как",
    "или",
    "это",
    "рынок",
    "будет",
}

ENTITY_ALIASES: dict[str, tuple[str, ...]] = {
    "iran": ("iran", "tehran"),
    "israel": ("israel", "jerusalem"),
    "trump": ("trump", "donald"),
    "china": ("china", "xi", "beijing"),
    "bitcoin": ("bitcoin", "btc"),
    "ethereum": ("ethereum", "eth"),
    "openai": ("openai", "chatgpt"),
    "anthropic": ("anthropic", "claude"),
    "nvidia": ("nvidia", "nvda"),
    "fed": ("fed", "federal reserve", "powell"),
    "peru": ("peru", "peruvian"),
}


@dataclass(frozen=True, slots=True)
class MarketEventMatch:
    event: ExternalNewsItem
    relevance_score: float
    match_reason: str


def _text_from_market(market: Any) -> str:
    if isinstance(market, Mapping):
        raw = market.get("raw") if isinstance(market.get("raw"), Mapping) else market
        parts = [
            market.get("title"),
            market.get("question"),
            market.get("slug"),
            market.get("category"),
            raw.get("description") if isinstance(raw, Mapping) else None,
            raw.get("eventTitle") if isinstance(raw, Mapping) else None,
        ]
    else:
        raw = getattr(market, "raw", {}) or {}
        parts = [
            getattr(market, "question", None),
            getattr(market, "slug", None),
            raw.get("category") if isinstance(raw, Mapping) else None,
            raw.get("description") if isinstance(raw, Mapping) else None,
            raw.get("eventTitle") if isinstance(raw, Mapping) else None,
        ]
    if isinstance(raw, Mapping):
        tags = raw.get("tags") or raw.get("tag")
        if isinstance(tags, Sequence) and not isinstance(tags, (str, bytes)):
            parts.extend(
                str(tag.get("label") or tag.get("name") or tag)
                if isinstance(tag, Mapping)
                else str(tag)
                for tag in tags
            )
    return " ".join(str(part) for part in parts if part)


def _tokens(text: str) -> set[str]:
    words = re.findall(r"[a-zA-ZА-Яа-я0-9][a-zA-ZА-Яа-я0-9_/-]{2,}", text.lower())
    return {word.strip("_/-") for word in words if word not in STOPWORDS and len(word) >= 3}


def _entities(tokens: set[str]) -> set[str]:
    found: set[str] = set()
    joined = " ".join(tokens)
    for entity, aliases in ENTITY_ALIASES.items():
        if any(alias in tokens or alias in joined for alias in aliases):
            found.add(entity)
    return found


def extract_market_terms(market: Any) -> dict[str, set[str]]:
    tokens = _tokens(_text_from_market(market))
    return {"tokens": tokens, "entities": _entities(tokens)}


def _event_terms(event: ExternalNewsItem) -> dict[str, set[str]]:
    tokens = _tokens(f"{event.title} {event.summary} {' '.join(event.topics)}")
    entities = set(event.entities) | _entities(tokens)
    return {"tokens": tokens, "entities": entities}


def score_event_relevance(market: Any, event: ExternalNewsItem) -> float:
    market_terms = extract_market_terms(market)
    event_terms = _event_terms(event)
    token_overlap = market_terms["tokens"] & event_terms["tokens"]
    entity_overlap = market_terms["entities"] & event_terms["entities"]

    # Source quality must not create relevance by itself. A trusted source about
    # another topic is still a weak match for this market.
    if not token_overlap and not entity_overlap:
        return 0.0

    score = 0.0
    score += min(42.0, len(token_overlap) * 7.0)
    score += min(42.0, len(entity_overlap) * 18.0)
    if event.category and event.category in _text_from_market(market).lower():
        score += 5.0
    if entity_overlap:
        score += min(8.0, event.urgency_score / 16)
        score += min(6.0, event.credibility_score / 20)
    elif len(token_overlap) >= 2:
        score += min(5.0, event.urgency_score / 24)
        score += min(4.0, event.credibility_score / 28)
    return round(min(100.0, score), 2)


def match_reason(market: Any, event: ExternalNewsItem) -> str:
    market_terms = extract_market_terms(market)
    event_terms = _event_terms(event)
    entities = sorted(market_terms["entities"] & event_terms["entities"])
    if entities:
        return f"matched entities: {', '.join(entities[:3])}"
    overlap = sorted(market_terms["tokens"] & event_terms["tokens"])
    if overlap:
        return f"matched terms: {', '.join(overlap[:4])}"
    return "category context"


def match_events_to_market(
    market: Any,
    events: Sequence[ExternalNewsItem],
    *,
    limit: int = 5,
    min_score: float = 18.0,
) -> list[MarketEventMatch]:
    matches = [
        MarketEventMatch(
            event=event,
            relevance_score=score,
            match_reason=match_reason(market, event),
        )
        for event in events
        if (score := score_event_relevance(market, event)) >= min_score
    ]
    return sorted(matches, key=lambda item: item.relevance_score, reverse=True)[:limit]
