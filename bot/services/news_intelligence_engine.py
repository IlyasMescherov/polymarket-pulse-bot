from __future__ import annotations

import asyncio
import logging
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Sequence

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.database.repositories import (
    link_market_event,
    upsert_external_event,
    upsert_external_source,
)
from bot.services.event_categories import classify_market_category
from bot.services.event_matching_engine import MarketEventMatch, match_events_to_market
from bot.services.source_adapters.base import ExternalNewsItem
from bot.services.source_adapters.news_api_adapter import NewsAPIAdapter
from bot.services.source_adapters.official_sources_adapter import OfficialSourcesAdapter
from bot.services.source_adapters.rss_adapter import RSSAdapter
from bot.services.source_adapters.telegram_public_adapter import TelegramPublicAdapter
from bot.services.source_adapters.x_adapter import XAdapter
from bot.services.source_credibility_engine import (
    credible_source_count,
    news_confidence,
    official_source_present,
    source_mix,
)

logger = logging.getLogger(__name__)


FALLBACK_NEWS: dict[str, dict[str, str]] = {
    "en": {
        "context": "No strong external news matched yet.",
        "why": "Market movement is not clearly tied to a verified external event yet.",
        "changed": "No major outside event matched this market yet.",
        "risk": "Check official sources before drawing a strong conclusion.",
        "top_reason": "No strong external match.",
    },
    "ru": {
        "context": "Сильных внешних новостей пока не найдено.",
        "why": "Движение рынка пока не связано с проверенным внешним событием.",
        "changed": "К этому рынку пока не найдено сильное внешнее событие.",
        "risk": "Перед сильным выводом проверь официальные источники.",
        "top_reason": "Сильной внешней связи пока нет.",
    },
}


@dataclass(frozen=True, slots=True)
class NewsContext:
    news_context: str
    latest_relevant_news: tuple[dict[str, Any], ...] = ()
    related_news: tuple[dict[str, Any], ...] = ()
    source_count: int = 0
    credible_source_count: int = 0
    social_heat: str = "low"
    telegram_heat: str = "low"
    x_heat: str = "low"
    official_source_signal: bool = False
    official_source_status: str = "No official source matched yet."
    news_urgency: str = "low"
    why_moving_now: str = ""
    what_changed_outside_market: str = ""
    confidence_from_news: str = "low"
    news_risk_note: str = ""
    news_count_24h: int = 0
    top_news_reason: str = ""
    source_mix: dict[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "news_context": self.news_context,
            "latest_relevant_news": list(self.latest_relevant_news),
            "related_news": list(self.related_news),
            "source_count": self.source_count,
            "credible_source_count": self.credible_source_count,
            "social_heat": self.social_heat,
            "telegram_heat": self.telegram_heat,
            "x_heat": self.x_heat,
            "official_source_signal": self.official_source_signal,
            "official_source_status": self.official_source_status,
            "news_urgency": self.news_urgency,
            "why_moving_now": self.why_moving_now,
            "what_changed_outside_market": self.what_changed_outside_market,
            "confidence_from_news": self.confidence_from_news,
            "news_risk_note": self.news_risk_note,
            "news_count_24h": self.news_count_24h,
            "top_news_reason": self.top_news_reason,
            "source_mix": dict(self.source_mix),
        }


def _lang(language: str | None) -> str:
    return "ru" if str(language or "").lower().startswith("ru") else "en"


def _heat(count: int) -> str:
    if count >= 5:
        return "high"
    if count >= 2:
        return "medium"
    return "low"


def _urgency(matches: Sequence[MarketEventMatch]) -> str:
    if not matches:
        return "low"
    score = max(match.event.urgency_score for match in matches)
    if score >= 70:
        return "high"
    if score >= 45:
        return "medium"
    return "low"


def _event_dict(match: MarketEventMatch) -> dict[str, Any]:
    event = match.event
    return {
        "title": event.title,
        "summary": event.summary,
        "url": event.url,
        "source": event.source_name,
        "source_type": event.source_type,
        "published_at": event.published_at.isoformat() if event.published_at else None,
        "category": event.category,
        "relevance_score": match.relevance_score,
        "match_reason": match.match_reason,
        "credibility_score": event.credibility_score,
    }


def _dedupe_key(event: ExternalNewsItem) -> str:
    title = " ".join(event.title.lower().split())
    url = event.url.split("?", 1)[0].rstrip("/")
    return url or f"{event.source_name}:{title}"


def dedupe_events(events: Iterable[ExternalNewsItem]) -> list[ExternalNewsItem]:
    deduped: dict[str, ExternalNewsItem] = {}
    for event in events:
        key = _dedupe_key(event)
        existing = deduped.get(key)
        if existing is None or event.credibility_score > existing.credibility_score:
            deduped[key] = event
    return list(deduped.values())


class NewsIntelligenceEngine:
    def __init__(
        self,
        *,
        enable_rss: bool = True,
        enable_official_sources: bool = True,
        enable_x_source: bool = False,
        enable_telegram_source: bool = False,
        news_api_key: str | None = None,
        seed_events: Sequence[ExternalNewsItem] | None = None,
        adapters: Sequence[Any] | None = None,
    ) -> None:
        self._events: list[ExternalNewsItem] = list(seed_events or [])
        self._last_refresh_at: datetime | None = None
        if adapters is not None:
            self._adapters = list(adapters)
        else:
            self._adapters = []
            if enable_rss:
                self._adapters.append(RSSAdapter())
            if enable_official_sources:
                self._adapters.append(OfficialSourcesAdapter())
            self._adapters.append(NewsAPIAdapter(news_api_key, enabled=bool(news_api_key)))
            self._adapters.append(XAdapter(enabled=enable_x_source))
            self._adapters.append(TelegramPublicAdapter(enabled=enable_telegram_source))

    @classmethod
    def from_settings(cls, settings: Any) -> "NewsIntelligenceEngine":
        return cls(
            enable_rss=bool(getattr(settings, "enable_rss_source", True)),
            enable_official_sources=bool(getattr(settings, "enable_official_sources", True)),
            enable_x_source=bool(getattr(settings, "enable_x_source", False)),
            enable_telegram_source=bool(getattr(settings, "enable_telegram_source", False)),
        )

    @property
    def events(self) -> tuple[ExternalNewsItem, ...]:
        return tuple(self._events)

    @property
    def last_refresh_at(self) -> datetime | None:
        return self._last_refresh_at

    async def close(self) -> None:
        for adapter in self._adapters:
            close = getattr(adapter, "close", None)
            if close is not None:
                await close()

    async def refresh(self) -> list[ExternalNewsItem]:
        batches = await asyncio.gather(
            *[adapter.fetch() for adapter in self._adapters],
            return_exceptions=True,
        )
        events: list[ExternalNewsItem] = []
        for batch in batches:
            if isinstance(batch, Exception):
                logger.info("News adapter failed: %s", batch)
                continue
            events.extend(item for item in batch if isinstance(item, ExternalNewsItem))
        self._events = sorted(
            dedupe_events(events),
            key=lambda item: item.published_at or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )[:300]
        self._last_refresh_at = datetime.now(timezone.utc)
        return list(self._events)

    def market_context(
        self,
        market: Any,
        *,
        language: str | None = None,
        events: Sequence[ExternalNewsItem] | None = None,
    ) -> NewsContext:
        return build_news_context(market, list(events if events is not None else self._events), language=language)

    def today_themes(
        self,
        markets: Sequence[Any],
        *,
        language: str | None = None,
        events: Sequence[ExternalNewsItem] | None = None,
    ) -> list[dict[str, Any]]:
        lang = _lang(language)
        material = list(events if events is not None else self._events)
        if not material:
            return [
                {
                    "theme": "Market watch" if lang == "en" else "Наблюдение за рынком",
                    "linked_markets": len(markets),
                    "latest_news": FALLBACK_NEWS[lang]["context"],
                    "why_it_matters": FALLBACK_NEWS[lang]["why"],
                    "confidence": "low",
                }
            ]

        category_counter: Counter[str] = Counter()
        latest_by_category: dict[str, ExternalNewsItem] = {}
        for event in material:
            category_counter[event.category or "global"] += 1
            latest_by_category.setdefault(event.category or "global", event)

        themes: list[dict[str, Any]] = []
        for category, count in category_counter.most_common(3):
            event = latest_by_category[category]
            linked = sum(1 for market in markets if _market_category(market) == category)
            themes.append(
                {
                    "theme": _category_title(category, lang),
                    "linked_markets": linked,
                    "latest_news": event.title,
                    "why_it_matters": _theme_reason(category, lang),
                    "confidence": news_confidence([event]),
                    "source": event.source_name,
                    "source_type": event.source_type,
                    "count": count,
                }
            )
        return themes


def build_news_context(
    market: Any,
    events: Sequence[ExternalNewsItem],
    *,
    language: str | None = None,
) -> NewsContext:
    lang = _lang(language)
    matches = match_events_to_market(market, events, limit=5)
    if not matches:
        fallback = FALLBACK_NEWS[lang]
        return NewsContext(
            news_context=fallback["context"],
            why_moving_now=fallback["why"],
            what_changed_outside_market=fallback["changed"],
            news_risk_note=fallback["risk"],
            top_news_reason=fallback["top_reason"],
            official_source_status=(
                "No official source matched yet."
                if lang == "en"
                else "Официального источника по теме пока нет."
            ),
        )

    matched_events = [match.event for match in matches]
    mix = source_mix(matched_events)
    official = official_source_present(matched_events)
    credible_count = credible_source_count(matched_events)
    confidence = news_confidence(matched_events)
    latest = tuple(_event_dict(match) for match in matches[:3])
    news_count_24h = _count_recent(matched_events)
    source_count = len({event.source_name for event in matched_events})
    social_count = mix.get("x", 0) + mix.get("telegram", 0)

    return NewsContext(
        news_context=_news_context_sentence(matches, lang),
        latest_relevant_news=latest,
        related_news=latest,
        source_count=source_count,
        credible_source_count=credible_count,
        social_heat=_heat(social_count),
        telegram_heat=_heat(mix.get("telegram", 0)),
        x_heat=_heat(mix.get("x", 0)),
        official_source_signal=official,
        official_source_status=(
            "Official source matched."
            if official and lang == "en"
            else "Есть официальный источник."
            if official
            else "No official source matched yet."
            if lang == "en"
            else "Официального источника по теме пока нет."
        ),
        news_urgency=_urgency(matches),
        why_moving_now=_why_moving_now(matches, lang),
        what_changed_outside_market=_what_changed(matches, lang),
        confidence_from_news=confidence,
        news_risk_note=_risk_note(official, confidence, lang),
        news_count_24h=news_count_24h,
        top_news_reason=matches[0].match_reason,
        source_mix=mix,
    )


class NewsRefreshJob:
    def __init__(
        self,
        engine: NewsIntelligenceEngine,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
        *,
        refresh_minutes: int = 10,
    ) -> None:
        self._engine = engine
        self._session_factory = session_factory
        self._refresh_delta = timedelta(minutes=max(1, int(refresh_minutes)))
        self._last_run_at: datetime | None = None

    async def run_due(self) -> None:
        now = datetime.now(timezone.utc)
        if self._last_run_at and now - self._last_run_at < self._refresh_delta:
            return
        self._last_run_at = now
        events = await self._engine.refresh()
        if self._session_factory is not None and events:
            await self._store_events(events)

    async def _store_events(self, events: Sequence[ExternalNewsItem]) -> None:
        try:
            async with self._session_factory() as session:
                for event in events:
                    source = await upsert_external_source(
                        session,
                        source_type=event.source_type,
                        name=event.source_name,
                        url=event.source_url,
                        credibility_score=event.credibility_score,
                        category=event.category,
                    )
                    await upsert_external_event(session, source, event)
                await session.commit()
        except Exception as exc:
            logger.info("Could not store external news events yet: %s", exc)


async def store_market_event_links(
    session: AsyncSession,
    market_id: str,
    matches: Sequence[MarketEventMatch],
) -> None:
    for match in matches:
        await link_market_event(
            session,
            market_id=market_id,
            event_url=match.event.url,
            relevance_score=match.relevance_score,
            match_reason=match.match_reason,
        )


def _count_recent(events: Sequence[ExternalNewsItem]) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    return sum(
        1
        for event in events
        if event.published_at is None or event.published_at >= cutoff
    )


def _category_title(category: str, lang: str) -> str:
    labels = {
        "en": {
            "politics": "Politics",
            "crypto": "Crypto",
            "sports": "Sports",
            "ai": "AI",
            "global": "Global events",
            "economy": "Economy",
        },
        "ru": {
            "politics": "Политика",
            "crypto": "Крипта",
            "sports": "Спорт",
            "ai": "AI",
            "global": "Мировые события",
            "economy": "Экономика",
        },
    }
    return labels[lang].get(category, category.replace("_", " ").title())


def _market_category(market: Any) -> str:
    try:
        return classify_market_category(market)
    except AttributeError:
        if isinstance(market, dict):
            text = " ".join(str(market.get(key) or "") for key in ("title", "question", "category", "slug")).lower()
            for category, terms in {
                "politics": ("trump", "iran", "election", "diplomacy", "president"),
                "crypto": ("bitcoin", "btc", "ethereum", "crypto"),
                "sports": ("nba", "nfl", "football", "match", "playoff"),
                "ai": ("openai", "anthropic", "nvidia", " ai "),
            }.items():
                if any(term in text for term in terms):
                    return category
        return "global"


def _theme_reason(category: str, lang: str) -> str:
    if lang == "ru":
        return {
            "politics": "Политические темы чаще требуют проверки официальных заявлений.",
            "crypto": "Крипторынки быстро реагируют на волатильность и новости компаний.",
            "sports": "Спортивные рынки чувствительны к расписанию и ближайшим матчам.",
            "ai": "AI-темы часто двигаются вокруг объявлений и новостного цикла.",
        }.get(category, "Эта тема стала заметнее во внешнем фоне.")
    return {
        "politics": "Political themes need official-source checks before strong conclusions.",
        "crypto": "Crypto markets react quickly to volatility and company news.",
        "sports": "Sports markets are sensitive to timing and near-term events.",
        "ai": "AI topics often move around announcements and news cycles.",
    }.get(category, "This theme became more visible in the external backdrop.")


def _news_context_sentence(matches: Sequence[MarketEventMatch], lang: str) -> str:
    top = matches[0].event
    source_count = len({match.event.source_name for match in matches})
    if lang == "ru":
        if top.source_type == "official":
            return f"Есть официальный источник по теме: {top.source_name}."
        if source_count >= 2:
            return f"Несколько источников пишут о той же теме."
        return f"Найден внешний материал по теме: {top.source_name}."
    if top.source_type == "official":
        return f"An official source is part of the backdrop: {top.source_name}."
    if source_count >= 2:
        return "Several sources are covering the same theme."
    return f"External context matched from {top.source_name}."


def _why_moving_now(matches: Sequence[MarketEventMatch], lang: str) -> str:
    top = matches[0].event
    if lang == "ru":
        if top.source_type == "official":
            return "Внешний фон стал серьёзнее, потому что появился официальный источник."
        if top.urgency_score >= 70:
            return "Тема стала срочной во внешнем новостном фоне."
        return "Внешний фон добавляет контекст, но сильного официального подтверждения пока нет."
    if top.source_type == "official":
        return "The outside backdrop is stronger because an official source is involved."
    if top.urgency_score >= 70:
        return "The topic became more urgent in the outside news backdrop."
    return "External coverage adds context, but official confirmation is still limited."


def _what_changed(matches: Sequence[MarketEventMatch], lang: str) -> str:
    top = matches[0].event
    if lang == "ru":
        return f"Последний внешний контекст: {top.title}"
    return f"Latest outside context: {top.title}"


def _risk_note(official: bool, confidence: str, lang: str) -> str:
    if lang == "ru":
        if official:
            return "Официальный источник есть, но всё равно проверь правила разрешения рынка."
        if confidence == "medium":
            return "Источников несколько, но официального подтверждения по теме пока нет."
        return "Новостной фон слабый. Не делай сильный вывод без проверки источников."
    if official:
        return "An official source is present, but resolution rules still matter."
    if confidence == "medium":
        return "There are multiple sources, but no official confirmation matched yet."
    return "The news backdrop is thin. Avoid a strong read without checking sources."
