from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from bot.services.event_matching_engine import MarketEventMatch, match_events_to_market
from bot.services.source_adapters.base import ExternalNewsItem
from bot.services.source_credibility_engine import (
    credible_source_count,
    news_confidence,
    official_source_present,
)
from bot.utils.i18n import normalize_language


IMPACT_LABELS: dict[str, dict[str, str]] = {
    "en": {
        "official_confirmed": "Official source confirmed",
        "multiple_sources": "Multiple sources cover this",
        "social_only": "Social-only context",
        "stale_context": "Stale context",
        "market_moved_without_news": "Market moved without strong news",
        "news_without_market_reaction": "News present, market barely reacted",
        "weak_external_context": "Weak external context",
    },
    "ru": {
        "official_confirmed": "Есть официальное подтверждение",
        "multiple_sources": "Несколько источников по теме",
        "social_only": "Только социальный фон",
        "stale_context": "Новость уже старая",
        "market_moved_without_news": "Рынок двинулся без сильного новостного фона",
        "news_without_market_reaction": "Новость есть, но рынок почти не отреагировал",
        "weak_external_context": "Внешний контекст слабый",
    },
}

CATALYST_LABELS: dict[str, dict[str, str]] = {
    "en": {
        "confirmed_catalyst": "Confirmed catalyst",
        "possible_catalyst": "Possible catalyst",
        "background_context": "Background context",
        "weak_signal": "Weak evidence",
        "no_clear_signal": "No clear catalyst",
    },
    "ru": {
        "confirmed_catalyst": "Подтверждённый катализатор",
        "possible_catalyst": "Возможный катализатор",
        "background_context": "Фоновый контекст",
        "weak_signal": "Слабое подтверждение",
        "no_clear_signal": "Ясного катализатора нет",
    },
}


@dataclass(frozen=True, slots=True)
class NewsImpact:
    impact_type: str
    impact_label: str
    confidence_level: str
    source_count: int
    official_source_signal: bool
    reason: str
    catalyst_type: str
    catalyst_label: str
    evidence_strength: str
    movement_explanation: str
    what_to_verify_next: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "news_impact_type": self.impact_type,
            "news_impact_label": self.impact_label,
            "news_impact_confidence": self.confidence_level,
            "news_impact_source_count": self.source_count,
            "news_impact_official_source": self.official_source_signal,
            "news_impact_reason": self.reason,
            "catalyst_type": self.catalyst_type,
            "catalyst_label": self.catalyst_label,
            "evidence_strength": self.evidence_strength,
            "movement_explanation": self.movement_explanation,
            "what_to_verify_next": list(self.what_to_verify_next),
        }


class NewsImpactEngine:
    """Classify whether outside information explains a market or story."""

    def classify_market(
        self,
        market: Any,
        events: Sequence[ExternalNewsItem],
        *,
        language: str | None = "en",
    ) -> NewsImpact:
        return classify_news_impact(
            market,
            events=events,
            language=language,
        )

    def classify_matches(
        self,
        matches: Sequence[MarketEventMatch],
        *,
        reaction_score: float = 0,
        language: str | None = "en",
    ) -> NewsImpact:
        return classify_news_impact_from_matches(
            matches,
            reaction_score=reaction_score,
            language=language,
        )


def classify_news_impact(
    market: Any,
    *,
    events: Sequence[ExternalNewsItem],
    language: str | None = "en",
    min_score: float = 18.0,
) -> NewsImpact:
    matches = match_events_to_market(market, events, limit=6, min_score=min_score)
    return classify_news_impact_from_matches(
        matches,
        reaction_score=_reaction_score(market),
        language=language,
    )


def classify_news_impact_from_matches(
    matches: Sequence[MarketEventMatch],
    *,
    reaction_score: float = 0,
    language: str | None = "en",
) -> NewsImpact:
    lang = normalize_language(language)
    events = [match.event for match in matches]
    source_count = len({event.source_name for event in events})
    official = official_source_present(events)
    social_only = bool(events) and all(event.source_type in {"x", "telegram"} for event in events)
    stale = bool(events) and all(_is_stale(event) for event in events)

    if official:
        impact_type = "official_confirmed"
    elif source_count >= 2 or credible_source_count(events) >= 2:
        impact_type = "multiple_sources"
    elif social_only:
        impact_type = "social_only"
    elif stale:
        impact_type = "stale_context"
    elif not events and reaction_score >= 55:
        impact_type = "market_moved_without_news"
    elif events and reaction_score < 30:
        impact_type = "news_without_market_reaction"
    else:
        impact_type = "weak_external_context"
    catalyst_type = _catalyst_type(
        impact_type,
        matches,
        reaction_score=reaction_score,
        official=official,
        source_count=source_count,
        social_only=social_only,
        stale=stale,
    )

    return NewsImpact(
        impact_type=impact_type,
        impact_label=IMPACT_LABELS[lang][impact_type],
        confidence_level=_impact_confidence(impact_type, events),
        source_count=source_count,
        official_source_signal=official,
        reason=_impact_reason(impact_type, lang),
        catalyst_type=catalyst_type,
        catalyst_label=CATALYST_LABELS[lang][catalyst_type],
        evidence_strength=_evidence_strength(catalyst_type, reaction_score, lang),
        movement_explanation=_movement_explanation(
            catalyst_type,
            impact_type,
            reaction_score,
            lang,
        ),
        what_to_verify_next=_what_to_verify_next(catalyst_type, lang),
    )


def _reaction_score(market: Any) -> float:
    pulse = _number(_get(market, "pulse_score")) or 0
    movement = abs(_number(_get(market, "movement")) or 0) * 2
    volume = _number(_get(market, "volume")) or _number(_get(market, "public_activity")) or 0
    volume_score = 0
    if volume >= 1_000_000:
        volume_score = 24
    elif volume >= 250_000:
        volume_score = 16
    elif volume >= 50_000:
        volume_score = 8
    return min(100.0, pulse + movement + volume_score)


def _impact_confidence(impact_type: str, events: Sequence[ExternalNewsItem]) -> str:
    if impact_type == "official_confirmed":
        return "high"
    if impact_type == "multiple_sources":
        return "medium" if news_confidence(events) != "high" else "high"
    if impact_type in {"social_only", "stale_context", "weak_external_context"}:
        return "low"
    if impact_type == "market_moved_without_news":
        return "low"
    return "medium"


def _impact_reason(impact_type: str, lang: str) -> str:
    en = {
        "official_confirmed": "A primary or official source is part of the story.",
        "multiple_sources": "Several sources are covering the same theme.",
        "social_only": "The outside context is mostly social discussion.",
        "stale_context": "Matched coverage is older, so freshness is limited.",
        "market_moved_without_news": "The market reaction is stronger than the matched outside context.",
        "news_without_market_reaction": "Coverage exists, but the market reaction remains limited.",
        "weak_external_context": "Outside context is present but not strong enough for a firm read.",
    }
    ru = {
        "official_confirmed": "В истории есть первичный или официальный источник.",
        "multiple_sources": "Несколько источников пишут об одной теме.",
        "social_only": "Внешний фон в основном социальный.",
        "stale_context": "Найденный контекст уже не самый свежий.",
        "market_moved_without_news": "Реакция рынка сильнее найденного внешнего контекста.",
        "news_without_market_reaction": "Новости есть, но реакция рынка ограничена.",
        "weak_external_context": "Внешний контекст есть, но он слабый для твёрдого вывода.",
    }
    return (ru if lang == "ru" else en)[impact_type]


def _catalyst_type(
    impact_type: str,
    matches: Sequence[MarketEventMatch],
    *,
    reaction_score: float,
    official: bool,
    source_count: int,
    social_only: bool,
    stale: bool,
) -> str:
    strongest_match = max((match.relevance_score for match in matches), default=0)
    if official and not stale and reaction_score >= 40 and strongest_match >= 45:
        return "confirmed_catalyst"
    if impact_type == "multiple_sources" and source_count >= 2 and reaction_score >= 40 and not stale:
        return "possible_catalyst"
    if impact_type == "news_without_market_reaction" or (matches and reaction_score < 30):
        return "background_context"
    if social_only or impact_type in {"social_only", "market_moved_without_news"}:
        return "weak_signal"
    if not matches:
        return "no_clear_signal"
    if stale:
        return "background_context"
    return "weak_signal"


def _evidence_strength(catalyst_type: str, reaction_score: float, lang: str) -> str:
    if lang == "ru":
        if catalyst_type == "confirmed_catalyst":
            return "Сильное подтверждение"
        if catalyst_type == "possible_catalyst":
            return "Среднее подтверждение"
        if catalyst_type == "background_context":
            return "Фоновое подтверждение"
        if reaction_score >= 55:
            return "Рынок движется сильнее источников"
        return "Слабое подтверждение"
    if catalyst_type == "confirmed_catalyst":
        return "Strong evidence"
    if catalyst_type == "possible_catalyst":
        return "Medium evidence"
    if catalyst_type == "background_context":
        return "Background evidence"
    if reaction_score >= 55:
        return "Market moved more than sources explain"
    return "Weak evidence"


def _movement_explanation(
    catalyst_type: str,
    impact_type: str,
    reaction_score: float,
    lang: str,
) -> str:
    if lang == "ru":
        if catalyst_type == "confirmed_catalyst":
            return "Движение связано с проверяемым внешним событием."
        if catalyst_type == "possible_catalyst":
            return "Движение совпало с несколькими источниками, но требует проверки."
        if catalyst_type == "background_context":
            return "Новостной фон есть, но рынок не показывает сильной реакции."
        if impact_type == "market_moved_without_news" or reaction_score >= 55:
            return "Рынок движется сильнее найденного внешнего фона."
        return "Ясной внешней причины пока не видно."
    if catalyst_type == "confirmed_catalyst":
        return "The move is tied to a verifiable outside event."
    if catalyst_type == "possible_catalyst":
        return "The move lines up with multiple sources, but still needs verification."
    if catalyst_type == "background_context":
        return "News context exists, but the market reaction is limited."
    if impact_type == "market_moved_without_news" or reaction_score >= 55:
        return "The market is moving more than the matched outside context explains."
    return "There is no clear outside catalyst yet."


def _what_to_verify_next(catalyst_type: str, lang: str) -> tuple[str, ...]:
    if lang == "ru":
        base = ["правила разрешения", "время до завершения"]
        if catalyst_type != "confirmed_catalyst":
            base.insert(0, "официальные источники")
        if catalyst_type in {"weak_signal", "no_clear_signal"}:
            base.append("связанные рынки")
        return tuple(base[:4])
    base = ["resolution rules", "time to resolution"]
    if catalyst_type != "confirmed_catalyst":
        base.insert(0, "official sources")
    if catalyst_type in {"weak_signal", "no_clear_signal"}:
        base.append("related markets")
    return tuple(base[:4])


def _is_stale(event: ExternalNewsItem) -> bool:
    if event.published_at is None:
        return False
    published_at = event.published_at
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - published_at).total_seconds() > 48 * 3600


def _get(source: Any, key: str) -> Any:
    if isinstance(source, dict):
        raw = source.get("raw") if isinstance(source.get("raw"), dict) else {}
        return source.get(key, raw.get(key))
    raw = getattr(source, "raw", None)
    if isinstance(raw, dict) and key in raw:
        return raw.get(key)
    return getattr(source, key, None)


def _number(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
