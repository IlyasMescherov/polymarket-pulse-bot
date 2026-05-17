from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from bot.services.source_adapters.base import ExternalNewsItem


STOPWORDS = {
    "a",
    "and",
    "an",
    "any",
    "are",
    "according",
    "about",
    "after",
    "again",
    "against",
    "all",
    "been",
    "before",
    "can",
    "candidate",
    "candidates",
    "could",
    "during",
    "event",
    "events",
    "for",
    "from",
    "has",
    "have",
    "how",
    "into",
    "is",
    "its",
    "known",
    "latest",
    "market",
    "markets",
    "may",
    "more",
    "national",
    "news",
    "not",
    "office",
    "official",
    "officials",
    "one",
    "or",
    "over",
    "presidential",
    "public",
    "should",
    "source",
    "than",
    "that",
    "the",
    "this",
    "through",
    "under",
    "was",
    "were",
    "what",
    "when",
    "where",
    "who",
    "will",
    "with",
    "whether",
    "why",
    "would",
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


def matched_terms_from_reason(reason: str) -> tuple[str, ...]:
    if "matched terms:" not in reason.lower():
        return ()
    raw = reason.split(":", 1)[1] if ":" in reason else ""
    terms = [term.strip().lower() for term in raw.split(",")]
    return tuple(term for term in terms if term and term not in STOPWORDS and len(term) >= 3)


def has_entity_match(match: MarketEventMatch) -> bool:
    return match.match_reason.lower().startswith("matched entities:")


def is_strong_official_match(match: MarketEventMatch) -> bool:
    return (
        match.event.source_type == "official"
        and has_entity_match(match)
        and match.relevance_score >= 45
    )


def is_related_news_match(match: MarketEventMatch) -> bool:
    if match.event.source_type == "official":
        return is_strong_official_match(match)
    if has_entity_match(match):
        return match.relevance_score >= 30
    terms = matched_terms_from_reason(match.match_reason)
    if len(terms) >= 3 and match.relevance_score >= 32:
        return True
    return len(terms) >= 2 and match.relevance_score >= 18


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


def _normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.lower())
    return "".join(char for char in normalized if not unicodedata.combining(char))


def _tokens(text: str) -> set[str]:
    words = re.findall(r"[\w/-]{2,}", _normalize_text(text), flags=re.UNICODE)
    return {
        word.strip("_/-")
        for word in words
        if word.strip("_/-")
        and word.strip("_/-") not in STOPWORDS
        and (len(word.strip("_/-")) >= 3 or word.strip("_/-") in {"ai", "us", "uk", "eu"})
    }


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


def overlap_terms(market: Any, event: ExternalNewsItem) -> dict[str, set[str]]:
    market_terms = extract_market_terms(market)
    event_terms = _event_terms(event)
    return {
        "tokens": market_terms["tokens"] & event_terms["tokens"],
        "entities": market_terms["entities"] & event_terms["entities"],
    }


def score_event_relevance(market: Any, event: ExternalNewsItem) -> float:
    market_terms = extract_market_terms(market)
    event_terms = _event_terms(event)
    token_overlap = market_terms["tokens"] & event_terms["tokens"]
    entity_overlap = market_terms["entities"] & event_terms["entities"]

    # Source quality must not create relevance by itself. A trusted source about
    # another topic is still a weak match for this market.
    if not token_overlap and not entity_overlap:
        return 0.0
    if event.source_type == "official" and not entity_overlap:
        return 0.0
    if not entity_overlap and len(token_overlap) < 2:
        return 0.0

    score = 0.0
    score += min(42.0, len(token_overlap) * 7.0)
    score += min(42.0, len(entity_overlap) * 18.0)
    if event.category and event.category in _text_from_market(market).lower():
        score += 5.0
    if entity_overlap:
        score += min(8.0, event.urgency_score / 16)
        score += min(6.0, event.credibility_score / 20)
    elif len(token_overlap) >= 3:
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
