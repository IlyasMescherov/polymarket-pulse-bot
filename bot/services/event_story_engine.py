from __future__ import annotations

import hashlib
import re
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from bot.services.event_categories import category_label, classify_market_category
from bot.services.event_matching_engine import (
    MarketEventMatch,
    extract_market_terms,
    match_events_to_market,
)
from bot.services.news_impact_engine import NewsImpact, classify_news_impact_from_matches
from bot.services.source_adapters.base import ExternalNewsItem
from bot.utils.i18n import normalize_language


@dataclass(frozen=True, slots=True)
class StoryCluster:
    story_cluster_id: str
    story_title: str
    story_summary: str
    primary_category: str
    linked_markets: tuple[dict[str, Any], ...]
    related_market_ids: tuple[str, ...]
    main_market_id: str
    dominant_outcome: str | None
    runner_up_outcome: str | None
    source_count: int
    official_source_signal: bool
    news_urgency: str
    market_reaction_score: float
    what_changed: str
    why_it_matters: str
    what_to_verify: tuple[str, ...]
    confidence_level: str
    news_impact_type: str
    news_impact_label: str
    catalyst_type: str
    catalyst_label: str
    what_happened: str
    affected_markets: tuple[str, ...]
    movement_timing: str
    likely_catalyst: str
    catalyst_evidence: str
    price_probability_context: str
    what_to_verify_next: tuple[str, ...]
    freshness_score: float
    story_quality_score: float
    is_story_qualified: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "story_cluster_id": self.story_cluster_id,
            "story_title": self.story_title,
            "story_summary": self.story_summary,
            "primary_category": self.primary_category,
            "linked_markets": list(self.linked_markets),
            "related_market_ids": list(self.related_market_ids),
            "main_market_id": self.main_market_id,
            "dominant_outcome": self.dominant_outcome,
            "runner_up_outcome": self.runner_up_outcome,
            "source_count": self.source_count,
            "official_source_signal": self.official_source_signal,
            "news_urgency": self.news_urgency,
            "market_reaction_score": self.market_reaction_score,
            "what_changed": self.what_changed,
            "why_it_matters": self.why_it_matters,
            "what_to_verify": list(self.what_to_verify),
            "confidence_level": self.confidence_level,
            "news_impact_type": self.news_impact_type,
            "news_impact_label": self.news_impact_label,
            "catalyst_type": self.catalyst_type,
            "catalyst_label": self.catalyst_label,
            "what_happened": self.what_happened,
            "affected_markets": list(self.affected_markets),
            "movement_timing": self.movement_timing,
            "likely_catalyst": self.likely_catalyst,
            "catalyst_evidence": self.catalyst_evidence,
            "price_probability_context": self.price_probability_context,
            "what_to_verify_next": list(self.what_to_verify_next),
            "freshness_score": self.freshness_score,
            "story_quality_score": self.story_quality_score,
            "is_story_qualified": self.is_story_qualified,
            "related_markets_count": len(self.related_market_ids),
        }


class EventStoryEngine:
    """Build event-level story clusters above individual Polymarket markets."""

    def build_stories(
        self,
        markets: Sequence[Any],
        *,
        market_api_objects: Sequence[dict[str, Any]] | None = None,
        events: Sequence[ExternalNewsItem] | None = None,
        language: str | None = "en",
        include_weak: bool = False,
    ) -> list[StoryCluster]:
        return build_event_stories(
            markets,
            market_api_objects=market_api_objects,
            events=events,
            language=language,
            include_weak=include_weak,
        )

    def enrich_markets(
        self,
        markets: Sequence[Any],
        market_api_objects: Sequence[dict[str, Any]],
        *,
        events: Sequence[ExternalNewsItem] | None = None,
        language: str | None = "en",
    ) -> tuple[list[dict[str, Any]], list[StoryCluster]]:
        stories = self.build_stories(
            markets,
            market_api_objects=market_api_objects,
            events=events,
            language=language,
        )
        enriched = enrich_markets_with_stories(market_api_objects, stories)
        return enriched, stories


def build_event_stories(
    markets: Sequence[Any],
    *,
    market_api_objects: Sequence[dict[str, Any]] | None = None,
    events: Sequence[ExternalNewsItem] | None = None,
    language: str | None = "en",
    include_weak: bool = False,
) -> list[StoryCluster]:
    lang = normalize_language(language)
    event_items = list(events or [])
    api_by_id = {
        str(item.get("market_id") or item.get("id") or ""): dict(item)
        for item in (market_api_objects or [])
        if item
    }

    groups: dict[str, list[Any]] = defaultdict(list)
    titles: dict[str, str] = {}
    for market in markets:
        key, title = _story_key_and_title(market, event_items)
        groups[key].append(market)
        titles.setdefault(key, title)

    clusters = [
        _build_cluster(
            story_key=key,
            title=titles[key],
            markets=group,
            api_by_id=api_by_id,
            events=event_items,
            lang=lang,
        )
        for key, group in groups.items()
    ]
    qualified = [cluster for cluster in clusters if cluster.is_story_qualified]
    result = clusters if include_weak else qualified
    return sorted(result, key=_story_rank, reverse=True)


def enrich_markets_with_stories(
    market_api_objects: Sequence[dict[str, Any]],
    stories: Sequence[StoryCluster],
) -> list[dict[str, Any]]:
    story_by_market: dict[str, StoryCluster] = {}
    for story in stories:
        for market_id in story.related_market_ids:
            story_by_market[market_id] = story

    enriched: list[dict[str, Any]] = []
    for item in market_api_objects:
        market_id = str(item.get("market_id") or item.get("id") or "")
        story = story_by_market.get(market_id)
        next_item = dict(item)
        if story is not None:
            next_item.update(
                {
                    "market_story_id": story.story_cluster_id,
                    "story_title": story.story_title,
                    "story_context": story.story_summary,
                    "news_impact_type": story.news_impact_type,
                    "news_impact_label": story.news_impact_label,
                    "catalyst_type": story.catalyst_type,
                    "catalyst_label": story.catalyst_label,
                    "story_what_happened": story.what_happened,
                    "story_affected_markets": list(story.affected_markets),
                    "movement_timing": story.movement_timing,
                    "likely_catalyst": story.likely_catalyst,
                    "catalyst_evidence": story.catalyst_evidence,
                    "price_probability_context": story.price_probability_context,
                    "what_to_verify_next": list(story.what_to_verify_next),
                    "what_changed_in_story": story.what_changed,
                    "related_markets_count": len(story.related_market_ids),
                }
            )
        enriched.append(next_item)
    return enriched


def select_top_story(stories: Sequence[StoryCluster]) -> dict[str, Any] | None:
    return stories[0].as_dict() if stories else None


def _build_cluster(
    *,
    story_key: str,
    title: str,
    markets: Sequence[Any],
    api_by_id: Mapping[str, dict[str, Any]],
    events: Sequence[ExternalNewsItem],
    lang: str,
) -> StoryCluster:
    linked = [_linked_market_payload(market, api_by_id) for market in markets]
    linked = sorted(linked, key=_market_reaction_score, reverse=True)
    main = linked[0]
    market_ids = tuple(str(item.get("market_id") or item.get("id")) for item in linked)
    categories = Counter(_market_category(market) for market in markets)
    primary_category = categories.most_common(1)[0][0] if categories else "global"
    matches = _cluster_matches(markets, events)
    impact = classify_news_impact_from_matches(
        matches,
        reaction_score=max(_market_reaction_score(item) for item in linked),
        language=lang,
    )
    source_count = len({match.event.source_name for match in matches})
    official = any(match.event.source_type == "official" for match in matches)
    urgency_score = max((match.event.urgency_score for match in matches), default=0)
    reaction = round(sum(_market_reaction_score(item) for item in linked) / max(1, len(linked)), 2)
    max_movement = max(abs(_number(item.get("movement")) or 0) for item in linked)
    confidence = _story_confidence(impact, linked_count=len(linked), reaction_score=reaction)
    freshness = _freshness_score(matches)
    quality = _story_quality_score(
        impact=impact,
        linked_count=len(linked),
        source_count=source_count,
        official=official,
        news_urgency=_urgency_label(urgency_score),
        reaction_score=reaction,
        freshness_score=freshness,
    )
    qualified = _passes_story_threshold(
        impact=impact,
        linked_count=len(linked),
        source_count=source_count,
        official=official,
        news_urgency=_urgency_label(urgency_score),
        freshness_score=freshness,
    )

    story_title = _clean_story_title(title) or _fallback_story_title(markets, primary_category, lang)
    return StoryCluster(
        story_cluster_id=_story_id(story_key),
        story_title=story_title,
        story_summary=_story_summary(
            story_title,
            linked_count=len(linked),
            impact=impact,
            lang=lang,
        ),
        primary_category=primary_category,
        linked_markets=tuple(linked[:5]),
        related_market_ids=market_ids,
        main_market_id=str(main.get("market_id") or main.get("id")),
        dominant_outcome=main.get("dominant_outcome_label") or main.get("dominant_side"),
        runner_up_outcome=main.get("runner_up_label"),
        source_count=source_count,
        official_source_signal=official,
        news_urgency=_urgency_label(urgency_score),
        market_reaction_score=reaction,
        what_changed=_what_changed(impact, linked_count=len(linked), reaction_score=reaction, lang=lang),
        why_it_matters=_why_it_matters(story_title, primary_category, impact, lang),
        what_to_verify=_what_to_verify(impact, lang),
        confidence_level=confidence,
        news_impact_type=impact.impact_type,
        news_impact_label=impact.impact_label,
        catalyst_type=impact.catalyst_type,
        catalyst_label=impact.catalyst_label,
        what_happened=_what_happened(
            story_title,
            linked_count=len(linked),
            impact=impact,
            reaction_score=reaction,
            lang=lang,
        ),
        affected_markets=tuple(str(item.get("title") or "") for item in linked[:3] if item.get("title")),
        movement_timing=_movement_timing(matches, linked, lang),
        likely_catalyst=_likely_catalyst(impact, matches, lang),
        catalyst_evidence=impact.evidence_strength,
        price_probability_context=_price_probability_context(
            linked,
            max_movement=max_movement,
            reaction_score=reaction,
            lang=lang,
        ),
        what_to_verify_next=impact.what_to_verify_next,
        freshness_score=freshness,
        story_quality_score=quality,
        is_story_qualified=qualified,
    )


def _story_key_and_title(market: Any, events: Sequence[ExternalNewsItem]) -> tuple[str, str]:
    raw = _raw(market)
    slug = str(raw.get("eventSlug") or "").strip()
    title = str(raw.get("eventTitle") or raw.get("groupItemTitle") or "").strip()
    if not slug and isinstance(raw.get("events"), list) and raw["events"]:
        first = raw["events"][0]
        if isinstance(first, Mapping):
            slug = str(first.get("slug") or "").strip()
            title = title or str(first.get("title") or "").strip()
    if slug:
        return f"event:{slug}", title or _market_title(market)
    if title:
        return f"event_title:{_slugify(title)}", title

    terms = extract_market_terms(market)
    entities = sorted(terms.get("entities", set()))
    if not entities:
        for match in match_events_to_market(market, events, limit=1, min_score=18):
            entities = sorted(str(entity) for entity in match.event.entities[:3])
            if entities:
                break
            topics = [str(topic) for topic in match.event.topics[:2] if str(topic).strip()]
            if topics:
                return f"news_topic:{_slugify('-'.join(topics))}", _entity_story_title(topics)
            if match.event.url:
                return f"news_event:{_story_id(match.event.url)}", match.event.title
    if entities:
        key_entities = _story_entities(entities)
        return f"entities:{'-'.join(key_entities)}", _entity_story_title(entities[:3])

    return f"market:{_market_id(market)}", _market_title(market)


def _cluster_matches(markets: Sequence[Any], events: Sequence[ExternalNewsItem]) -> list[MarketEventMatch]:
    by_url: dict[str, MarketEventMatch] = {}
    for market in markets:
        for match in match_events_to_market(market, events, limit=5, min_score=18):
            current = by_url.get(match.event.url)
            if current is None or match.relevance_score > current.relevance_score:
                by_url[match.event.url] = match
    return sorted(by_url.values(), key=lambda item: item.relevance_score, reverse=True)[:8]


def _linked_market_payload(market: Any, api_by_id: Mapping[str, dict[str, Any]]) -> dict[str, Any]:
    market_id = _market_id(market)
    payload = dict(api_by_id.get(market_id) or {})
    if not payload:
        payload = {
            "market_id": market_id,
            "title": _market_title(market),
            "category": _market_category(market),
            "probability": _percent(_get(market, "yes_probability")),
            "volume": _get(market, "volume"),
            "url": _get(market, "url"),
        }
    payload.setdefault("market_id", market_id)
    payload.setdefault("title", _market_title(market))
    payload.setdefault("category", _market_category(market))
    return payload


def _market_reaction_score(item: Mapping[str, Any]) -> float:
    pulse = _number(item.get("pulse_score")) or 0
    movement = abs(_number(item.get("movement")) or 0) * 2
    volume = _number(item.get("volume")) or _number(item.get("public_activity")) or 0
    news = {"high": 18, "medium": 10, "low": 0}.get(str(item.get("news_urgency") or "low").lower(), 0)
    volume_score = 0
    if volume >= 1_000_000:
        volume_score = 22
    elif volume >= 250_000:
        volume_score = 14
    elif volume >= 50_000:
        volume_score = 7
    return min(100.0, pulse + movement + volume_score + news)


def _story_rank(story: StoryCluster) -> float:
    urgency = {"high": 30, "medium": 16, "low": 0}.get(story.news_urgency, 0)
    official = 18 if story.official_source_signal else 0
    linked = min(20, len(story.related_market_ids) * 6)
    sources = min(14, story.source_count * 4)
    freshness = min(12, story.freshness_score)
    quality = min(20, story.story_quality_score / 5)
    return story.market_reaction_score + urgency + official + linked + sources + freshness + quality


def _story_confidence(impact: NewsImpact, *, linked_count: int, reaction_score: float) -> str:
    if impact.confidence_level == "high":
        return "high"
    if linked_count >= 2 and impact.confidence_level in {"medium", "high"}:
        return "medium"
    if reaction_score >= 70 and linked_count >= 2:
        return "medium"
    return "low"


def _passes_story_threshold(
    *,
    impact: NewsImpact,
    linked_count: int,
    source_count: int,
    official: bool,
    news_urgency: str,
    freshness_score: float,
) -> bool:
    if linked_count >= 2:
        return True
    if official:
        return True
    strong_news = (
        impact.impact_type in {"official_confirmed", "multiple_sources"}
        and source_count >= 2
        and news_urgency in {"high", "medium"}
        and freshness_score > 0
    )
    return strong_news


def _story_quality_score(
    *,
    impact: NewsImpact,
    linked_count: int,
    source_count: int,
    official: bool,
    news_urgency: str,
    reaction_score: float,
    freshness_score: float,
) -> float:
    urgency = {"high": 24, "medium": 12, "low": 0}.get(news_urgency, 0)
    impact_weight = {
        "official_confirmed": 28,
        "multiple_sources": 18,
        "social_only": 5,
        "stale_context": 3,
        "market_moved_without_news": 6,
        "news_without_market_reaction": 5,
        "weak_external_context": 0,
    }.get(impact.impact_type, 0)
    return round(
        min(
            100.0,
            linked_count * 14
            + min(16, source_count * 4)
            + (22 if official else 0)
            + urgency
            + impact_weight
            + min(12, freshness_score)
            + min(16, reaction_score / 5),
        ),
        2,
    )


def _freshness_score(matches: Sequence[MarketEventMatch]) -> float:
    now = datetime.now(timezone.utc)
    scores: list[float] = []
    for match in matches:
        published_at = match.event.published_at
        if published_at is None:
            continue
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)
        hours = max(0.0, (now - published_at).total_seconds() / 3600)
        if hours <= 6:
            scores.append(12)
        elif hours <= 24:
            scores.append(8)
        elif hours <= 48:
            scores.append(4)
    return max(scores, default=0)


def _story_summary(title: str, *, linked_count: int, impact: NewsImpact, lang: str) -> str:
    if lang == "ru":
        if linked_count > 1:
            return f"История объединяет {linked_count} рынков. {impact.impact_label}."
        return f"Одиночный рынок в теме: {title}. {impact.impact_label}."
    if linked_count > 1:
        return f"This story links {linked_count} markets. {impact.impact_label}."
    return f"Single-market story: {title}. {impact.impact_label}."


def _what_happened(
    title: str,
    *,
    linked_count: int,
    impact: NewsImpact,
    reaction_score: float,
    lang: str,
) -> str:
    if lang == "ru":
        if impact.catalyst_type == "confirmed_catalyst":
            return f"{title}: появился проверяемый внешний контекст, и рынок отреагировал заметнее обычного."
        if linked_count >= 2:
            return f"{title}: несколько связанных рынков стали частью одной истории."
        if reaction_score >= 65:
            return f"{title}: рынок выделился сильнее найденного внешнего фона."
        return f"{title}: история пока формируется вокруг одного рынка."
    if impact.catalyst_type == "confirmed_catalyst":
        return f"{title}: verifiable outside context appeared and the market reaction became more visible."
    if linked_count >= 2:
        return f"{title}: several related markets now sit inside the same story."
    if reaction_score >= 65:
        return f"{title}: the market reaction is stronger than the matched outside context."
    return f"{title}: the story is still forming around one market."


def _what_changed(impact: NewsImpact, *, linked_count: int, reaction_score: float, lang: str) -> str:
    if lang == "ru":
        if impact.impact_type == "official_confirmed":
            return "В истории появился официальный контекст."
        if linked_count > 1:
            return "Несколько связанных рынков попали в одну историю."
        if impact.impact_type == "market_moved_without_news" or reaction_score >= 70:
            return "Рынок реагирует сильнее найденного внешнего фона."
        return "История пока формируется."
    if impact.impact_type == "official_confirmed":
        return "Official context entered the story."
    if linked_count > 1:
        return "Several related markets now sit inside one story."
    if impact.impact_type == "market_moved_without_news" or reaction_score >= 70:
        return "Market reaction is stronger than the matched outside context."
    return "The story is still forming."


def _movement_timing(
    matches: Sequence[MarketEventMatch],
    linked: Sequence[Mapping[str, Any]],
    lang: str,
) -> str:
    freshness = _freshness_score(matches)
    ending_soon = sum(
        1
        for item in linked
        if str(item.get("time_pressure_key") or "").lower() == "ending_soon"
        or "ending" in str(item.get("market_mood") or "").lower()
    )
    if lang == "ru":
        if ending_soon:
            return "Часть рынков близка к завершению, поэтому реакция может быть краткосрочной."
        if freshness >= 8:
            return "Свежий внешний контекст совпал с текущим рыночным движением."
        return "Движение не выглядит привязанным к очень свежему источнику."
    if ending_soon:
        return "Some linked markets are near resolution, so the reaction may be short-term."
    if freshness >= 8:
        return "Fresh outside context lines up with the current market move."
    return "The move is not clearly tied to a very fresh source."


def _likely_catalyst(impact: NewsImpact, matches: Sequence[MarketEventMatch], lang: str) -> str:
    if matches:
        top = matches[0].event
        source = top.source_name or top.source_type
        if lang == "ru":
            if impact.catalyst_type == "confirmed_catalyst":
                return f"Главный кандидат: {source}, официальный или первичный источник."
            if impact.catalyst_type == "possible_catalyst":
                return f"Возможный катализатор: несколько источников, включая {source}."
            if impact.catalyst_type == "background_context":
                return f"Фон: {source}, но реакция рынка ограничена."
            return f"Проверить источник: {source}."
        if impact.catalyst_type == "confirmed_catalyst":
            return f"Likely catalyst: {source}, a primary or official source."
        if impact.catalyst_type == "possible_catalyst":
            return f"Possible catalyst: multiple sources, including {source}."
        if impact.catalyst_type == "background_context":
            return f"Background source: {source}, with limited market reaction."
        return f"Source to verify: {source}."
    return (
        "Ясного внешнего катализатора пока не найдено."
        if lang == "ru"
        else "No clear outside catalyst has been matched yet."
    )


def _price_probability_context(
    linked: Sequence[Mapping[str, Any]],
    *,
    max_movement: float,
    reaction_score: float,
    lang: str,
) -> str:
    strong_volume = any((_number(item.get("volume")) or 0) >= 250_000 for item in linked)
    if lang == "ru":
        if max_movement >= 5 and strong_volume:
            return "Вероятность и объём двигаются вместе, поэтому реакция выглядит сильнее."
        if max_movement >= 5:
            return "Вероятность сдвинулась, но объём нужно проверить отдельно."
        if reaction_score >= 65:
            return "Рынки заметны по активности, но вероятность меняется умеренно."
        return "Вероятности пока не показывают резкой переоценки."
    if max_movement >= 5 and strong_volume:
        return "Probability and volume are moving together, which makes the reaction stronger."
    if max_movement >= 5:
        return "Probability moved, but volume still needs a separate check."
    if reaction_score >= 65:
        return "Markets are visible through activity, while probability movement is moderate."
    return "Probabilities do not show a sharp repricing yet."


def _why_it_matters(title: str, category: str, impact: NewsImpact, lang: str) -> str:
    category_name = category_label(category, lang)
    if lang == "ru":
        if impact.impact_type == "official_confirmed":
            return f"{title} важна, потому что рынок получил более проверяемый внешний контекст."
        return f"{title} помогает понять, как {category_name.lower()} отражается в связанных рынках."
    if impact.impact_type == "official_confirmed":
        return f"{title} matters because the market now has more verifiable outside context."
    return f"{title} helps explain how {category_name.lower()} is showing up across related markets."


def _what_to_verify(impact: NewsImpact, lang: str) -> tuple[str, ...]:
    if lang == "ru":
        items = ["правила разрешения", "связанные рынки", "время до завершения"]
        if impact.impact_type != "official_confirmed":
            items.insert(0, "официальные источники")
        return tuple(items[:4])
    items = ["resolution rules", "related markets", "time to resolution"]
    if impact.impact_type != "official_confirmed":
        items.insert(0, "official sources")
    return tuple(items[:4])


def _fallback_story_title(markets: Sequence[Any], category: str, lang: str) -> str:
    entities = sorted(set().union(*(extract_market_terms(market).get("entities", set()) for market in markets)))
    if entities:
        return _entity_story_title(entities[:3])
    if len(markets) == 1:
        return _market_title(markets[0])
    return f"{category_label(category, lang)} market story"


def _entity_story_title(entities: Sequence[str]) -> str:
    labels = {
        "iran": "Iran",
        "israel": "Israel",
        "trump": "Trump",
        "china": "China",
        "bitcoin": "Bitcoin volatility",
        "ethereum": "Ethereum",
        "openai": "OpenAI",
        "anthropic": "Anthropic",
        "nvidia": "Nvidia",
        "fed": "Fed rate expectations",
    }
    named = [labels.get(entity, entity.replace("_", " ").title()) for entity in entities[:3]]
    if {"Iran", "Trump"}.issubset(set(named)) or {"Iran", "China"}.issubset(set(named)):
        return "Iran / US diplomacy"
    if named == ["Bitcoin volatility"]:
        return "Bitcoin volatility"
    return " / ".join(named)


def _story_entities(entities: Sequence[str]) -> list[str]:
    material = [str(entity).lower() for entity in entities]
    priority = ("iran", "israel", "bitcoin", "ethereum", "fed", "openai", "nvidia", "trump", "china")
    for entity in priority:
        if entity in material:
            return [entity]
    return sorted(material)[:2]


def _urgency_label(score: float) -> str:
    if score >= 70:
        return "high"
    if score >= 45:
        return "medium"
    return "low"


def _story_id(value: str) -> str:
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:12]
    return f"story_{digest}"


def _slugify(value: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "-", str(value).lower()).strip("-")
    return text or "story"


def _clean_story_title(value: str) -> str:
    text = " ".join(str(value or "").split())
    return text[:96]


def _raw(source: Any) -> Mapping[str, Any]:
    if isinstance(source, Mapping):
        raw = source.get("raw")
        return raw if isinstance(raw, Mapping) else source
    raw = getattr(source, "raw", None)
    return raw if isinstance(raw, Mapping) else {}


def _get(source: Any, key: str) -> Any:
    if isinstance(source, Mapping):
        raw = source.get("raw") if isinstance(source.get("raw"), Mapping) else {}
        return source.get(key, raw.get(key))
    return getattr(source, key, None)


def _market_id(market: Any) -> str:
    return str(_get(market, "market_id") or _get(market, "id") or _get(market, "slug") or _market_title(market))


def _market_title(market: Any) -> str:
    return str(_get(market, "title") or _get(market, "question") or "Untitled market").strip()


def _market_category(market: Any) -> str:
    if isinstance(market, Mapping):
        explicit = _normalize_category(market.get("category"))
        if explicit:
            return explicit
        title = _market_title(market).lower()
        if _contains_story_keyword(title, ("award", "oscars", "grammy", "movie", "film", "music", "celebrity")):
            return "culture"
        if _contains_story_keyword(title, ("bitcoin", "btc", "ethereum", "crypto", "binance")):
            return "crypto"
        if _contains_story_keyword(title, ("nba", "nfl", "ufc", "soccer", "football", "tennis", "match", "playoff")):
            return "sports"
        if _contains_story_keyword(title, ("openai", "nvidia", "anthropic", "ai")):
            return "ai"
        if _contains_story_keyword(title, ("iran", "israel", "trump", "election", "president", "war", "diplomacy")):
            return "politics"
        return "global"
    try:
        return classify_market_category(market)
    except Exception:
        return "global"


def _normalize_category(value: Any) -> str | None:
    key = str(value or "").strip().lower().replace(" ", "_")
    aliases = {
        "political": "politics",
        "politics": "politics",
        "crypto": "crypto",
        "cryptocurrency": "crypto",
        "ai": "ai",
        "ai_tech": "ai",
        "sports": "sports",
        "sport": "sports",
        "esports": "esports",
        "global": "global",
        "culture": "culture",
        "media": "culture",
        "entertainment": "culture",
    }
    return aliases.get(key)


def _contains_story_keyword(text: str, keywords: tuple[str, ...]) -> bool:
    for keyword in keywords:
        normalized = keyword.strip().lower()
        if not normalized:
            continue
        if " " in normalized or "." in normalized:
            if normalized in text:
                return True
            continue
        if re.search(rf"(?<![a-z0-9]){re.escape(normalized)}(?![a-z0-9])", text):
            return True
    return False


def _number(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _percent(value: Any) -> int | None:
    number = _number(value)
    if number is None:
        return None
    return round(number * 100 if 0 <= number <= 1 else number)
