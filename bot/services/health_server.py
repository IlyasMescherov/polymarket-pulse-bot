from __future__ import annotations

import asyncio
import copy
import logging
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from aiohttp import web
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.database.db import ping_database
from bot.database.models import BriefingCache, ExternalEvent
from bot.database.repositories import (
    get_briefing_cache,
    get_last_good_briefing_cache,
    get_latest_snapshots,
    get_recent_external_events,
    get_recent_snapshots,
    upsert_briefing_cache,
)
from bot.services.ai_context_engine import AIContextEngine, MarketContext
from bot.services.ai_insight_engine import generate_market_briefing
from bot.services.ai_output_schema import market_insight_schema
from bot.services.ai_quality_engine import score_ai_output
from bot.services.event_categories import category_label, classify_market_category
from bot.services.event_story_engine import (
    EventStoryEngine,
    enrich_markets_with_stories,
    select_top_story,
)
from bot.services.market_analyzer import MarketAnalyzer, MarketMovement
from bot.services.market_health import calculate_market_health
from bot.services.market_indicators import calculate_market_indicators
from bot.services.market_mood import calculate_market_mood
from bot.services.market_side_engine import analyze_market_side
from bot.services.news_intelligence_engine import (
    NewsContext,
    NewsIntelligenceEngine,
    build_news_context,
)
from bot.services.polymarket_client import Market
from bot.services.pulse_score import calculate_pulse_score
from bot.services.risk_flags import market_risk_flags
from bot.services.source_adapters.base import ExternalNewsItem
from bot.services.smart_money_analyzer import (
    MarketActivity,
    SmartMoneyAnalyzer,
    TraderScore,
)
from bot.services.today_pulse import TodayPulseItem, build_today_pulse_items
from bot.utils.formatting import format_probability

logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
LANDING_DIR = PROJECT_ROOT / "landing"
MINIAPP_DIR = PROJECT_ROOT / "miniapp"
TODAY_CACHE_KEY = "today:global:en"
DISCOVERY_TIMEOUT_SECONDS = 4.0
CACHE_METADATA_KEYS = {
    "is_cached",
    "is_stale",
    "generated_at",
    "updated_ago_seconds",
    "refresh_status",
}


def landing_asset_path(filename: str) -> Path:
    return LANDING_DIR / filename


def miniapp_asset_path(filename: str) -> Path:
    return MINIAPP_DIR / filename


def _percent(value: float | None) -> int | None:
    if value is None:
        return None
    return round(value * 100)


def _iso_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _duration_ms(start: float) -> int:
    return round((time.perf_counter() - start) * 1000)


def _empty_today_timings() -> dict[str, int | bool]:
    return {
        "total_ms": 0,
        "fetch_markets_ms": 0,
        "news_ms": 0,
        "story_ms": 0,
        "ai_ms": 0,
        "serialize_ms": 0,
        "cache_hit": False,
        "ai_quality_avg": 0,
        "ai_fallback_count": 0,
        "ai_parse_error_count": 0,
    }


def _strip_cache_metadata(payload: dict[str, Any]) -> dict[str, Any]:
    clean = copy.deepcopy(payload)
    for key in CACHE_METADATA_KEYS:
        clean.pop(key, None)
    return clean


def _probability_interpretation(value: float | None) -> str:
    if value is None:
        return "Unknown"
    percent = value * 100
    if percent < 15:
        return "Unlikely"
    if percent < 45:
        return "Possible"
    if percent < 75:
        return "Likely"
    return "Highly likely"


def _market_to_api_object(
    market: Market,
    delta: float | None = None,
    context: MarketContext | None = None,
    news_context: NewsContext | None = None,
) -> dict[str, Any]:
    pulse = calculate_pulse_score(market, delta=delta)
    health = calculate_market_health(market)
    mood = calculate_market_mood(market, delta=delta, language="en")
    indicators = calculate_market_indicators(
        market,
        pulse_score=pulse.value,
        delta=delta,
        language="en",
    )
    side = analyze_market_side(
        market,
        delta=delta,
        confirmation_level=indicators.confirmation_level_key,
        language="en",
    )
    category = context.category if context is not None else classify_market_category(market)
    news_fields = (
        news_context.as_dict()
        if news_context is not None
        else build_news_context(market, [], language="en").as_dict()
    )
    result = {
        "market_id": market.id,
        "title": market.question,
        "probability": _percent(market.yes_probability),
        "probability_label": format_probability(market.yes_probability, "en"),
        "probability_interpretation": (
            context.probability_interpretation
            if context is not None
            else _probability_interpretation(market.yes_probability)
        ),
        "volume": market.volume,
        "end_date": _iso_datetime(market.end_date),
        "movement": _percent(delta),
        "pulse_score": pulse.value,
        "pulse_label": pulse.label,
        "market_health_score": health.value,
        "market_health_label": health.label,
        "pulse_description": "How interesting this market looks today.",
        "market_health_description": "How clean and readable the market looks.",
        "market_mood": mood.key,
        "market_mood_label": mood.label,
        "market_mood_reason": mood.reason,
        "market_mood_reasoning": (
            context.market_mood_reasoning if context is not None else mood.reason
        ),
        "category": category,
        "category_label": context.category_label if context is not None else category_label(category, "en"),
        "quick_take": (
            context.quick_take
            if context is not None
            else "The market stands out enough to review."
        ),
        "why_people_care": (
            context.why_people_care
            if context is not None
            else "The market stands out enough to review."
        ),
        "simple_read": (
            context.simple_read
            if context is not None
            else "This market asks whether the event in the title will happen."
        ),
        "what_to_watch": (
            context.what_to_watch
            if context is not None
            else "Watch probability changes, public activity, time left, and resolution rules."
        ),
        "attention_summary": (
            context.attention_summary if context is not None else "No major shift yet."
        ),
        "topic_narrative": (
            context.topic_narrative
            if context is not None
            else f"{category_label(category, 'en')} markets are part of today’s attention map."
        ),
        "what_this_means": (
            context.what_this_means
            if context is not None
            else "This market is one clue in today’s attention picture."
        ),
        "what_happened": (
            context.what_happened if context is not None else "The market is becoming more visible."
        ),
        "main_tension": (
            context.main_tension
            if context is not None
            else "The market stands out, but the read still needs confirmation."
        ),
        "attention_vs_conviction": (
            context.attention_vs_conviction
            if context is not None
            else "Attention is present, but expectations have not clearly shifted."
        ),
        "insight_strength": (
            context.insight_strength if context is not None else "Interest is present"
        ),
        "confidence_level": (
            context.confidence_level if context is not None else "Low confidence"
        ),
        "what_to_check": (
            [item.strip() for item in context.what_to_watch.split(";") if item.strip()]
            if context is not None
            else ["Official resolution rules", "Volume quality"]
        ),
        "resolution_note": (
            context.resolution_note
            if context is not None
            else "Open the market page and read the official resolution criteria."
        ),
        "category_voice": (
            context.category_voice
            if context is not None
            else f"{category_label(category, 'en')} markets need a separate read."
        ),
        "related_topics": list(context.related_topics) if context is not None else [],
        "market_memory_summary": (
            context.market_memory_summary
            if context is not None
            else "Not enough history for comparison yet."
        ),
        "market_regime": (
            context.market_regime
            if context is not None
            else "Quiet market"
        ),
        "market_regime_key": (
            context.market_regime_key
            if context is not None
            else "quiet"
        ),
        "regime_reason": (
            context.regime_reason
            if context is not None
            else "There is not enough activity for a strong comparison yet."
        ),
        "memory_pattern": (
            context.memory_pattern
            if context is not None
            else "Not enough history for comparison yet."
        ),
        "changed_since_last_seen": (
            context.changed_since_last_seen
            if context is not None
            else "Not enough history for comparison yet."
        ),
        "historical_context": (
            context.historical_context
            if context is not None
            else "Not enough history for comparison yet."
        ),
        **side.as_dict(),
        **indicators.as_dict(),
        **news_fields,
        "risk_flags": market_risk_flags(market, delta=delta),
        "url": market.url,
    }
    quality = score_ai_output(
        {
            key: result.get(key)
            for key in (
                "quick_take",
                "why_people_care",
                "what_happened",
                "main_tension",
                "what_this_means",
                "attention_vs_conviction",
                "insight_strength",
                "resolution_note",
                "category_voice",
            )
        },
        schema=market_insight_schema,
        context={
            "title": market.question,
            "category": category,
            "dominant_outcome": result.get("dominant_outcome_label")
            or result.get("dominant_side"),
        },
    )
    result["ai_quality_score"] = quality.score
    result["ai_quality_flags"] = list(quality.flags)
    return result


def _category_from_title(title: str) -> str:
    text = title.lower()
    if _title_has_keyword(text, ("bitcoin", "btc", "ethereum", "crypto", "binance")):
        return "crypto"
    if _title_has_keyword(text, ("award", "oscars", "grammy", "movie", "film", "music", "celebrity")):
        return "culture"
    if _title_has_keyword(text, ("iran", "israel", "trump", "election", "president", "war", "diplomacy")):
        return "politics"
    if _title_has_keyword(text, ("nba", "nfl", "ufc", "soccer", "football", "tennis", "match", "playoff")):
        return "sports"
    if _title_has_keyword(text, ("openai", "nvidia", "anthropic", "ai")):
        return "ai"
    return "global"


def _title_has_keyword(text: str, keywords: tuple[str, ...]) -> bool:
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


def _attention_reason_for_title(title: str) -> str:
    category = _category_from_title(title)
    return {
        "crypto": "Crypto volatility made this market more visible.",
        "politics": "Political headlines made this market more visible.",
        "sports": "Event timing made this market more visible.",
        "ai": "AI news flow made this topic more visible today.",
        "culture": "Culture attention made this market more visible.",
        "global": "This market became more visible in the public activity layer.",
    }[category]


def _today_item_to_api_object(item: TodayPulseItem) -> dict[str, Any]:
    result = _market_to_api_object(item.market, item.delta)
    result["why_it_matters"] = item.why_it_matters
    result["why_people_care"] = result["market_mood_reason"]
    return result


def _external_event_to_news_item(event: ExternalEvent) -> ExternalNewsItem | None:
    raw = event.raw_payload or {}
    source_name = str(raw.get("source_name") or "External source")
    source_type = str(raw.get("source_type") or "rss")
    source_url = str(raw.get("source_url") or event.url)
    if not event.title or not event.url:
        return None
    entities = event.entities.get("items", []) if isinstance(event.entities, dict) else []
    topics = event.topics.get("items", []) if isinstance(event.topics, dict) else []
    return ExternalNewsItem(
        source_type=source_type,
        source_name=source_name,
        source_url=source_url,
        title=event.title,
        summary=event.summary or "",
        url=event.url,
        published_at=event.published_at,
        category=event.category or "global",
        entities=tuple(str(item) for item in entities),
        topics=tuple(str(item) for item in topics),
        sentiment=event.sentiment,
        urgency_score=event.urgency_score,
        credibility_score=event.credibility_score,
        raw_payload=raw,
    )


def _market_movement_to_api_object(item: MarketMovement) -> dict[str, Any]:
    return _market_to_api_object(item.market, item.delta)


def _smart_market_to_api_object(activity: MarketActivity) -> dict[str, Any]:
    category = _category_from_title(activity.market_title)
    briefing = generate_market_briefing(
        {
            "title": activity.market_title,
            "category": category,
            "public_activity": activity.amount_usd,
            "volume": activity.amount_usd,
            "probability_delta": 0,
            "probability": 0,
            "pulse_score": 55,
        },
        "en",
    )
    indicators = calculate_market_indicators(
        {
            "title": activity.market_title,
            "public_activity": activity.amount_usd,
            "volume": activity.amount_usd,
            "movement": 0,
            "pulse_score": 55,
        },
        pulse_score=55,
        delta=0,
        language="en",
    )
    side = analyze_market_side(
        {
            "title": activity.market_title,
            "probability": 0,
            "public_activity": activity.amount_usd,
            "volume": activity.amount_usd,
            "movement": 0,
        },
        delta=0,
        confirmation_level=indicators.confirmation_level_key,
        language="en",
    )
    return {
        "market_id": activity.market_id,
        "title": activity.market_title,
        "public_activity": round(activity.amount_usd, 2),
        "trades_count": activity.trades_count,
        "top_side": None,
        "probability": 0,
        "probability_label": "Unlikely",
        "probability_interpretation": "Unlikely",
        "pulse_score": 55,
        "pulse_label": "Worth watching",
        "url": "https://polymarket.com",
        "quick_take": briefing["quick_take"],
        "why_it_matters": _attention_reason_for_title(activity.market_title),
        "attention_summary": briefing["what_happened"],
        "what_happened": briefing["what_happened"],
        "main_tension": briefing["main_tension"],
        "what_this_means": briefing["what_this_means"],
        "attention_vs_conviction": briefing["attention_vs_conviction"],
        "insight_strength": briefing["insight_strength"],
        "confidence_level": briefing["confidence_level"],
        "what_to_check": briefing["what_to_check"],
        "resolution_note": briefing["resolution_note"],
        "category_voice": briefing["category_voice"],
        "market_memory_summary": briefing["market_memory_summary"],
        "market_regime": briefing["market_regime"],
        "market_regime_key": "short_term_attention",
        "regime_reason": briefing["regime_reason"],
        "memory_pattern": briefing["memory_pattern"],
        "changed_since_last_seen": briefing["changed_since_last_seen"],
        "historical_context": briefing["historical_context"],
        "related_topics": briefing["related_topics"],
        "category": category,
        "category_label": category_label(category, "en"),
        **side.as_dict(),
        **indicators.as_dict(),
        **build_news_context({"title": activity.market_title, "category": category}, [], language="en").as_dict(),
    }


def _trader_to_api_object(trader: TraderScore) -> dict[str, Any]:
    wallet = trader.wallet_address or ""
    short_wallet = f"{wallet[:6]}...{wallet[-4:]}" if len(wallet) >= 12 else wallet or None
    return {
        "wallet": short_wallet,
        "wallet_label": short_wallet,
        "trader_score": trader.score,
        "label": trader.label,
        "why_it_matters": "This wallet has been active across public Polymarket markets today.",
        "public_volume": trader.volume,
        "rank": trader.rank,
    }


class HealthServer:
    def __init__(
        self,
        host: str,
        port: int,
        engine: AsyncEngine,
        market_analyzer: MarketAnalyzer | None = None,
        smart_money_analyzer: SmartMoneyAnalyzer | None = None,
        ai_context_engine: AIContextEngine | None = None,
        news_intelligence_engine: NewsIntelligenceEngine | None = None,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
        today_refresh_minutes: int = 5,
        today_cache_ttl_seconds: int = 300,
        today_stale_max_seconds: int = 3600,
        enable_today_background_refresh: bool = True,
    ) -> None:
        self._host = host
        self._port = port
        self._engine = engine
        self._market_analyzer = market_analyzer
        self._smart_money_analyzer = smart_money_analyzer
        self._ai_context_engine = ai_context_engine or AIContextEngine(None)
        self._news_intelligence_engine = news_intelligence_engine or NewsIntelligenceEngine(
            enable_rss=False,
            enable_official_sources=False,
        )
        self._event_story_engine = EventStoryEngine()
        self._session_factory = session_factory
        self._runner: web.AppRunner | None = None
        self._today_refresh_minutes = max(1, int(today_refresh_minutes))
        self._today_cache_ttl_seconds = max(30, int(today_cache_ttl_seconds))
        self._today_stale_max_seconds = max(
            self._today_cache_ttl_seconds,
            int(today_stale_max_seconds),
        )
        self._enable_today_background_refresh = bool(enable_today_background_refresh)
        self._today_refresh_lock = asyncio.Lock()
        self._today_refresh_task: asyncio.Task[Any] | None = None
        self._today_periodic_task: asyncio.Task[Any] | None = None

    async def start(self) -> None:
        app = web.Application()
        app.router.add_get("/", self._landing_index)
        app.router.add_get("/landing", self._landing_index)
        app.router.add_get("/landing/", self._landing_index)
        app.router.add_get("/styles.css", self._landing_styles)
        app.router.add_get("/landing/styles.css", self._landing_styles)
        app.router.add_get("/health", self._health)
        app.router.add_get("/app", self._miniapp_index)
        app.router.add_get("/app/", self._miniapp_index)
        app.router.add_get("/app/styles.css", self._miniapp_styles)
        app.router.add_get("/app/app.js", self._miniapp_script)
        app.router.add_get("/api/today", self._api_today)
        app.router.add_get("/api/markets/hot", self._api_hot_markets)
        app.router.add_get("/api/markets/new", self._api_new_markets)
        app.router.add_get("/api/markets/moves", self._api_moves)
        app.router.add_get("/api/smart-money/active", self._api_smart_money_active)
        app.router.add_get("/api/smart-money/traders", self._api_smart_money_traders)
        app.router.add_get("/api/search", self._api_search)

        self._runner = web.AppRunner(app)
        await self._runner.setup()
        site = web.TCPSite(self._runner, host=self._host, port=self._port)
        await site.start()
        logger.info("Web endpoint started on %s:%s", self._host, self._port)
        if (
            self._enable_today_background_refresh
            and self._session_factory is not None
            and self._market_analyzer is not None
        ):
            self._today_periodic_task = asyncio.create_task(self._today_refresh_loop())

    async def stop(self) -> None:
        for task in (self._today_refresh_task, self._today_periodic_task):
            if task is not None:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        self._today_refresh_task = None
        self._today_periodic_task = None
        if self._runner is not None:
            await self._runner.cleanup()
            self._runner = None

    async def _health(self, request: web.Request) -> web.Response:
        try:
            await ping_database(self._engine)
        except Exception as exc:
            logger.warning("Health check failed: %s", exc)
            return web.json_response(
                {
                    "status": "error",
                    "service": "pulsemarket-bot",
                    "database": "unavailable",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                status=503,
            )

        return web.json_response(
            {
                "status": "ok",
                "service": "pulsemarket-bot",
                "database": "ok",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    async def _landing_index(self, request: web.Request) -> web.StreamResponse:
        index_path = landing_asset_path("index.html")
        if not index_path.exists():
            return web.Response(text="Landing page is not available.", status=404)
        return web.FileResponse(index_path)

    async def _landing_styles(self, request: web.Request) -> web.StreamResponse:
        styles_path = landing_asset_path("styles.css")
        if not styles_path.exists():
            return web.Response(text="Stylesheet is not available.", status=404)
        return web.FileResponse(styles_path)

    async def _miniapp_index(self, request: web.Request) -> web.StreamResponse:
        index_path = miniapp_asset_path("index.html")
        if not index_path.exists():
            return web.Response(text="Mini App is not available.", status=404)
        return web.FileResponse(index_path)

    async def _miniapp_styles(self, request: web.Request) -> web.StreamResponse:
        styles_path = miniapp_asset_path("styles.css")
        if not styles_path.exists():
            return web.Response(text="Mini App stylesheet is not available.", status=404)
        return web.FileResponse(styles_path)

    async def _miniapp_script(self, request: web.Request) -> web.StreamResponse:
        script_path = miniapp_asset_path("app.js")
        if not script_path.exists():
            return web.Response(text="Mini App script is not available.", status=404)
        return web.FileResponse(script_path)

    def _api_empty(self, message: str) -> web.Response:
        return web.json_response({"data": [], "message": message})

    async def _cached_today_data(self, limit: int = 5) -> list[dict[str, Any]]:
        if self._session_factory is None:
            return []
        try:
            async with self._session_factory() as session:
                cache_item = await get_last_good_briefing_cache(session, TODAY_CACHE_KEY)
        except Exception as exc:
            logger.debug("Could not load cached today data: %s", exc)
            return []
        payload = cache_item.payload_json if cache_item is not None else {}
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, list):
            return []
        return [dict(item) for item in data[:limit] if isinstance(item, dict)]

    def _cached_search_results(
        self,
        items: list[dict[str, Any]],
        query: str,
        *,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        terms = {term for term in re.findall(r"[a-zA-ZА-Яа-я0-9]{3,}", query.lower())}
        if not terms:
            return []
        matches: list[dict[str, Any]] = []
        for item in items:
            haystack = " ".join(
                str(value or "")
                for value in (
                    item.get("title"),
                    item.get("story_title"),
                    item.get("category"),
                    item.get("category_label"),
                    " ".join(str(topic) for topic in item.get("related_topics", []) if topic),
                )
            ).lower()
            if any(term in haystack for term in terms):
                matches.append(item)
        return matches[:limit]

    async def _market_history(self, market_id: str) -> list[Any]:
        if self._session_factory is None:
            return []
        try:
            async with self._session_factory() as session:
                return await get_recent_snapshots(session, market_id, limit=48)
        except Exception as exc:
            logger.debug("Could not load market memory for %s: %s", market_id, exc)
            return []

    async def _external_news_events(self) -> list[ExternalNewsItem]:
        if self._session_factory is None:
            return list(self._news_intelligence_engine.events)
        try:
            async with self._session_factory() as session:
                events = await get_recent_external_events(session, limit=250, since_hours=36)
        except Exception as exc:
            logger.debug("Could not load external news events: %s", exc)
            return list(self._news_intelligence_engine.events)
        converted = [_external_event_to_news_item(event) for event in events]
        return [item for item in converted if item is not None] or list(self._news_intelligence_engine.events)

    async def _market_news_context(self, market: Market) -> NewsContext:
        return self._news_intelligence_engine.market_context(
            market,
            language="en",
            events=await self._external_news_events(),
        )

    async def _market_api_object(
        self,
        market: Market,
        delta: float | None = None,
    ) -> dict[str, Any]:
        pulse = calculate_pulse_score(market, delta=delta)
        mood = calculate_market_mood(market, delta=delta, language="en")
        context = await self._ai_context_engine.market_context(
            market,
            pulse,
            mood,
            delta=delta,
            language="en",
            history=await self._market_history(market.id),
        )
        result = _market_to_api_object(market, delta, context=context)
        result.update((await self._market_news_context(market)).as_dict())
        result["why_it_matters"] = context.why_people_care
        return result

    async def _market_api_object_fast(
        self,
        market: Market,
        delta: float | None = None,
        *,
        events: list[ExternalNewsItem] | None = None,
    ) -> dict[str, Any]:
        pulse = calculate_pulse_score(market, delta=delta)
        mood = calculate_market_mood(market, delta=delta, language="en")
        context = self._ai_context_engine.fallback_market_context(
            market,
            pulse,
            mood,
            delta=delta,
            language="en",
            history=[],
        )
        news_context = self._news_intelligence_engine.market_context(
            market,
            language="en",
            events=events if events is not None else list(self._news_intelligence_engine.events),
        )
        result = _market_to_api_object(market, delta, context=context, news_context=news_context)
        result["why_it_matters"] = context.why_people_care
        return result

    async def _safe_market_context(
        self,
        item: TodayPulseItem,
        *,
        timings: dict[str, int | bool],
    ) -> MarketContext | None:
        start = time.perf_counter()
        mood = calculate_market_mood(item.market, delta=item.delta, language="en")
        history = await self._market_history(item.market.id)
        try:
            return await self._ai_context_engine.market_context(
                item.market,
                item.pulse_score,
                mood,
                delta=item.delta,
                language="en",
                history=history,
            )
        except asyncio.TimeoutError as exc:
            logger.warning("Today market AI context failed ai_timeout=true: %s", exc)
        except Exception as exc:
            logger.warning("Today market AI context failed: %s", exc)
        finally:
            timings["ai_ms"] = int(timings.get("ai_ms", 0)) + _duration_ms(start)

        fallback = getattr(self._ai_context_engine, "fallback_market_context", None)
        if callable(fallback):
            try:
                return fallback(
                    item.market,
                    item.pulse_score,
                    mood,
                    delta=item.delta,
                    language="en",
                    history=history,
                )
            except Exception as exc:
                logger.debug("Today market fallback context failed: %s", exc)
        return None

    async def _safe_daily_narrative(
        self,
        markets: list[Market],
        contexts: list[MarketContext],
        *,
        timings: dict[str, int | bool],
    ) -> Any:
        start = time.perf_counter()
        try:
            return await self._ai_context_engine.daily_narrative(
                markets,
                contexts,
                language="en",
            )
        except asyncio.TimeoutError as exc:
            logger.warning("Today narrative generation failed ai_timeout=true: %s", exc)
        except Exception as exc:
            logger.warning("Today narrative generation failed: %s", exc)
        finally:
            timings["ai_ms"] = int(timings.get("ai_ms", 0)) + _duration_ms(start)

        fallback = getattr(self._ai_context_engine, "fallback_daily_narrative", None)
        if callable(fallback):
            return fallback(markets, contexts, language="en")
        return type(
            "FallbackNarrative",
            (),
            {
                "headline": "There is no dominant market narrative today.",
                "interpretation": "There is not enough fresh market activity to build a clear read yet.",
                "what_changed": ("No clear theme yet.",),
                "category_summaries": {},
            },
        )()

    async def _today_items(self, timings: dict[str, int | bool]) -> list[TodayPulseItem]:
        if self._market_analyzer is None:
            return []
        start = time.perf_counter()
        hot_markets = await self._market_analyzer.get_hot_markets(limit=20)
        new_markets = await self._market_analyzer.get_new_markets(limit=10)
        markets = [*hot_markets, *new_markets]
        latest = {}
        if self._session_factory is not None and markets:
            async with self._session_factory() as session:
                latest = await get_latest_snapshots(session, [market.id for market in markets])
        timings["fetch_markets_ms"] = _duration_ms(start)
        return build_today_pulse_items(
            markets,
            latest_snapshots=latest,
            limit=5,
            language="en",
        )

    async def _today_api_payload(
        self,
        items: list[TodayPulseItem],
        timings: dict[str, int | bool] | None = None,
    ) -> dict[str, Any]:
        timings = timings if timings is not None else _empty_today_timings()
        data: list[dict[str, Any]] = []
        contexts: list[MarketContext] = []
        markets = [item.market for item in items]
        news_start = time.perf_counter()
        external_events = await self._external_news_events()
        timings["news_ms"] = int(timings.get("news_ms", 0)) + _duration_ms(news_start)
        for item in items:
            context = await self._safe_market_context(item, timings=timings)
            if context is not None:
                contexts.append(context)
            news_context = self._news_intelligence_engine.market_context(
                item.market,
                language="en",
                events=external_events,
            )
            result = _market_to_api_object(
                item.market,
                item.delta,
                context=context,
                news_context=news_context,
            )
            if context is not None:
                result["why_it_matters"] = context.why_people_care
            data.append(result)

        story_start = time.perf_counter()
        try:
            stories = self._event_story_engine.build_stories(
                markets,
                market_api_objects=data,
                events=external_events,
                language="en",
            )
            data = enrich_markets_with_stories(data, stories)
        except Exception as exc:
            logger.warning("Today story generation failed, using market fallback: %s", exc)
            stories = []
        timings["story_ms"] = _duration_ms(story_start)

        narrative = await self._safe_daily_narrative(
            [item.market for item in items],
            contexts,
            timings=timings,
        )
        serialize_start = time.perf_counter()
        news_theme_start = time.perf_counter()
        news_themes = self._news_intelligence_engine.today_themes(
            [item.market for item in items],
            language="en",
            events=external_events,
        )
        timings["news_ms"] = int(timings.get("news_ms", 0)) + _duration_ms(news_theme_start)
        payload = {
            "data": data,
            "message": "ok",
            "narrative": narrative.headline,
            "interpretation": narrative.interpretation,
            "what_changed": list(narrative.what_changed),
            "changed_since_last_brief": [
                context.changed_since_last_seen
                for context in contexts[:3]
                if context.changed_since_last_seen
            ],
            "category_summaries": narrative.category_summaries,
            "news_themes": news_themes,
            "top_story": select_top_story(stories),
            "story_clusters": [story.as_dict() for story in stories],
        }
        quality_scores = [
            int(item["ai_quality_score"])
            for item in data
            if isinstance(item.get("ai_quality_score"), int)
        ]
        if quality_scores:
            payload["ai_quality_avg"] = round(sum(quality_scores) / len(quality_scores))
        timings["serialize_ms"] = int(timings.get("serialize_ms", 0)) + _duration_ms(serialize_start)
        return payload

    async def _build_today_briefing_payload(
        self,
        timings: dict[str, int | bool] | None = None,
    ) -> dict[str, Any]:
        timings = timings if timings is not None else _empty_today_timings()
        if hasattr(self._ai_context_engine, "reset_quality_stats"):
            self._ai_context_engine.reset_quality_stats()
        items = await self._today_items(timings)
        payload = await self._today_api_payload(items, timings=timings)
        self._merge_ai_quality_stats(payload, timings)
        return payload

    def _merge_ai_quality_stats(
        self,
        payload: dict[str, Any],
        timings: dict[str, int | bool],
    ) -> None:
        stats = (
            self._ai_context_engine.quality_stats()
            if hasattr(self._ai_context_engine, "quality_stats")
            else {}
        )
        payload_quality = payload.get("ai_quality_avg")
        timings["ai_quality_avg"] = int(
            payload_quality if isinstance(payload_quality, int) else stats.get("ai_quality_avg", 0)
        )
        timings["ai_fallback_count"] = int(stats.get("ai_fallback_count", 0))
        timings["ai_parse_error_count"] = int(stats.get("ai_parse_error_count", 0))

    @staticmethod
    def _set_cached_quality_timing(
        payload: dict[str, Any],
        timings: dict[str, int | bool],
    ) -> None:
        quality = payload.get("ai_quality_avg")
        if isinstance(quality, int):
            timings["ai_quality_avg"] = quality

    def _cache_fresh(self, item: BriefingCache, now: datetime | None = None) -> bool:
        current = now or _utcnow()
        expires_at = _aware(item.expires_at)
        return expires_at is not None and expires_at > current

    def _cache_within_stale_window(
        self,
        item: BriefingCache,
        now: datetime | None = None,
    ) -> bool:
        current = now or _utcnow()
        generated_at = _aware(item.updated_at) or _aware(item.created_at)
        if generated_at is None:
            return False
        return (current - generated_at).total_seconds() <= self._today_stale_max_seconds

    def _with_cache_metadata(
        self,
        payload: dict[str, Any],
        *,
        cache_item: BriefingCache | None,
        is_cached: bool,
        is_stale: bool,
        refresh_status: str,
        generated_at: datetime | None = None,
    ) -> dict[str, Any]:
        current = _utcnow()
        resolved_generated_at = (
            _aware(generated_at)
            or (_aware(cache_item.updated_at) if cache_item is not None else None)
            or (_aware(cache_item.created_at) if cache_item is not None else None)
            or current
        )
        result = copy.deepcopy(payload)
        result.update(
            {
                "is_cached": is_cached,
                "is_stale": is_stale,
                "generated_at": resolved_generated_at.isoformat(),
                "updated_ago_seconds": max(
                    0,
                    round((current - resolved_generated_at).total_seconds()),
                ),
                "refresh_status": refresh_status,
            }
        )
        return {
            **result,
        }

    def _log_today_timing(self, timings: dict[str, int | bool]) -> None:
        logger.info(
            "today_perf today.total_ms=%s today.fetch_markets_ms=%s "
            "today.news_ms=%s today.story_ms=%s today.ai_ms=%s "
            "today.serialize_ms=%s today.cache_hit=%s today.ai_quality_avg=%s "
            "today.ai_fallback_count=%s today.ai_parse_error_count=%s",
            timings.get("total_ms", 0),
            timings.get("fetch_markets_ms", 0),
            timings.get("news_ms", 0),
            timings.get("story_ms", 0),
            timings.get("ai_ms", 0),
            timings.get("serialize_ms", 0),
            str(bool(timings.get("cache_hit", False))).lower(),
            timings.get("ai_quality_avg", 0),
            timings.get("ai_fallback_count", 0),
            timings.get("ai_parse_error_count", 0),
        )

    async def _save_today_cache(
        self,
        payload: dict[str, Any],
        *,
        cache_key: str = TODAY_CACHE_KEY,
    ) -> BriefingCache | None:
        if self._session_factory is None:
            return None
        clean_payload = _strip_cache_metadata(payload)
        expires_at = _utcnow() + timedelta(seconds=self._today_cache_ttl_seconds)
        async with self._session_factory() as session:
            item = await upsert_briefing_cache(
                session,
                cache_key=cache_key,
                payload_json=clean_payload,
                expires_at=expires_at,
                status="ready",
            )
            await session.commit()
            return item

    async def refresh_today_cache(self, *, reason: str = "scheduled") -> dict[str, Any] | None:
        if self._market_analyzer is None or self._session_factory is None:
            return None
        async with self._today_refresh_lock:
            timings = _empty_today_timings()
            start = time.perf_counter()
            try:
                payload = await self._build_today_briefing_payload(timings)
                await self._save_today_cache(payload)
                timings["total_ms"] = _duration_ms(start)
                timings["cache_hit"] = False
                self._log_today_timing(timings)
                logger.info("Today briefing cache refreshed reason=%s", reason)
                return payload
            except Exception as exc:
                timings["total_ms"] = _duration_ms(start)
                timings["cache_hit"] = False
                self._log_today_timing(timings)
                logger.warning("Today briefing refresh failed reason=%s: %s", reason, exc)
                return None

    def _schedule_today_refresh(self, *, reason: str) -> None:
        if (
            not self._enable_today_background_refresh
            or self._market_analyzer is None
            or self._session_factory is None
        ):
            return
        if self._today_refresh_task is not None and not self._today_refresh_task.done():
            return
        self._today_refresh_task = asyncio.create_task(self.refresh_today_cache(reason=reason))

    async def _today_refresh_loop(self) -> None:
        await asyncio.sleep(2)
        interval_seconds = max(60, self._today_refresh_minutes * 60)
        while True:
            try:
                await self.refresh_today_cache(reason="background_interval")
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Today background refresh loop failed")
            await asyncio.sleep(interval_seconds)

    async def _api_today(self, request: web.Request) -> web.Response:
        if self._market_analyzer is None:
            return self._api_empty("market analyzer unavailable")
        request_start = time.perf_counter()
        timings = _empty_today_timings()
        cache_key = TODAY_CACHE_KEY
        if self._session_factory is not None:
            try:
                async with self._session_factory() as session:
                    cache_item = await get_briefing_cache(session, cache_key)
                    now = _utcnow()
                    if cache_item is not None and self._cache_fresh(cache_item, now):
                        serialize_start = time.perf_counter()
                        payload = self._with_cache_metadata(
                            cache_item.payload_json,
                            cache_item=cache_item,
                            is_cached=True,
                            is_stale=False,
                            refresh_status="fresh",
                        )
                        self._set_cached_quality_timing(payload, timings)
                        timings["serialize_ms"] = _duration_ms(serialize_start)
                        timings["cache_hit"] = True
                        timings["total_ms"] = _duration_ms(request_start)
                        self._log_today_timing(timings)
                        return web.json_response(payload)

                    if cache_item is not None and self._cache_within_stale_window(cache_item, now):
                        self._schedule_today_refresh(reason="stale_request")
                        serialize_start = time.perf_counter()
                        payload = self._with_cache_metadata(
                            cache_item.payload_json,
                            cache_item=cache_item,
                            is_cached=True,
                            is_stale=True,
                            refresh_status="updating",
                        )
                        self._set_cached_quality_timing(payload, timings)
                        timings["serialize_ms"] = _duration_ms(serialize_start)
                        timings["cache_hit"] = True
                        timings["total_ms"] = _duration_ms(request_start)
                        self._log_today_timing(timings)
                        return web.json_response(payload)
            except Exception as exc:
                logger.warning("Today cache lookup failed: %s", exc)

        try:
            payload = await self._build_today_briefing_payload(timings)
            cache_item = await self._save_today_cache(payload, cache_key=cache_key)
            response_payload = self._with_cache_metadata(
                payload,
                cache_item=cache_item,
                is_cached=False,
                is_stale=False,
                refresh_status="fresh",
                generated_at=_utcnow(),
            )
            timings["cache_hit"] = False
            timings["total_ms"] = _duration_ms(request_start)
            self._log_today_timing(timings)
            return web.json_response(response_payload)
        except Exception as exc:
            logger.warning("Mini App Today API failed: %s", exc)
            if self._session_factory is not None:
                try:
                    async with self._session_factory() as session:
                        last_good = await get_last_good_briefing_cache(session, cache_key)
                    if last_good is not None:
                        payload = self._with_cache_metadata(
                            last_good.payload_json,
                            cache_item=last_good,
                            is_cached=True,
                            is_stale=True,
                            refresh_status="last_good",
                        )
                        self._set_cached_quality_timing(payload, timings)
                        timings["cache_hit"] = True
                        timings["total_ms"] = _duration_ms(request_start)
                        self._log_today_timing(timings)
                        return web.json_response(payload)
                except Exception as fallback_exc:
                    logger.warning("Today last-good cache fallback failed: %s", fallback_exc)
            timings["total_ms"] = _duration_ms(request_start)
            self._log_today_timing(timings)
            return self._api_empty("today pulse unavailable")

    async def _api_hot_markets(self, request: web.Request) -> web.Response:
        if self._market_analyzer is None:
            return self._api_empty("market analyzer unavailable")
        try:
            markets = await asyncio.wait_for(
                self._market_analyzer.get_hot_markets(limit=5),
                timeout=DISCOVERY_TIMEOUT_SECONDS,
            )
            events = await self._external_news_events()
            data = [
                await self._market_api_object_fast(market, events=events)
                for market in markets
            ]
            return web.json_response(
                {"data": data, "message": "ok"}
            )
        except asyncio.TimeoutError:
            cached = await self._cached_today_data(limit=5)
            logger.warning("Mini App hot markets API timed out; returning cached today fallback")
            return web.json_response(
                {
                    "data": cached,
                    "message": "cached market focus" if cached else "hot markets unavailable",
                    "is_cached": bool(cached),
                    "fallback": True,
                }
            )
        except Exception as exc:
            logger.warning("Mini App hot markets API failed: %s", exc)
            cached = await self._cached_today_data(limit=5)
            if cached:
                return web.json_response(
                    {
                        "data": cached,
                        "message": "cached market focus",
                        "is_cached": True,
                        "fallback": True,
                    }
                )
            return self._api_empty("hot markets unavailable")

    async def _api_new_markets(self, request: web.Request) -> web.Response:
        if self._market_analyzer is None:
            return self._api_empty("market analyzer unavailable")
        try:
            markets = await self._market_analyzer.get_new_markets(limit=5)
            data = [await self._market_api_object(market) for market in markets]
            return web.json_response(
                {"data": data, "message": "ok"}
            )
        except Exception as exc:
            logger.warning("Mini App new markets API failed: %s", exc)
            return self._api_empty("new markets unavailable")

    async def _api_moves(self, request: web.Request) -> web.Response:
        if self._market_analyzer is None or self._session_factory is None:
            return self._api_empty("movement data unavailable")
        try:
            async with self._session_factory() as session:
                movements = await self._market_analyzer.detect_movements(
                    session,
                    limit=50,
                    threshold=0.10,
                )
            return web.json_response(
                {
                    "data": [
                        await self._market_api_object(item.market, delta=item.delta)
                        for item in movements[:5]
                    ],
                    "message": "ok",
                }
            )
        except Exception as exc:
            logger.warning("Mini App moves API failed: %s", exc)
            return self._api_empty("sharp moves unavailable")

    async def _api_smart_money_active(self, request: web.Request) -> web.Response:
        if self._smart_money_analyzer is None:
            return self._api_empty("smart money analyzer unavailable")
        try:
            activities = await self._smart_money_analyzer.active_markets(limit=5)
            return web.json_response(
                {
                    "data": [_smart_market_to_api_object(activity) for activity in activities],
                    "message": "ok" if activities else "no active public markets above threshold",
                }
            )
        except Exception as exc:
            logger.warning("Mini App smart money active API failed: %s", exc)
            return self._api_empty("smart money active markets unavailable")

    async def _api_smart_money_traders(self, request: web.Request) -> web.Response:
        if self._smart_money_analyzer is None:
            return self._api_empty("smart money analyzer unavailable")
        try:
            traders = await self._smart_money_analyzer.public_traders(limit=5)
            return web.json_response(
                {"data": [_trader_to_api_object(trader) for trader in traders], "message": "ok"}
            )
        except Exception as exc:
            logger.warning("Mini App smart money traders API failed: %s", exc)
            return self._api_empty("public traders unavailable")

    async def _api_search(self, request: web.Request) -> web.Response:
        if self._market_analyzer is None:
            return self._api_empty("market analyzer unavailable")
        query = request.query.get("q", "").strip()
        if not query:
            return self._api_empty("search query is empty")
        try:
            markets = await asyncio.wait_for(
                self._market_analyzer.search_markets(query, limit=5),
                timeout=DISCOVERY_TIMEOUT_SECONDS,
            )
            events = await self._external_news_events()
            data = [
                await self._market_api_object_fast(market, events=events)
                for market in markets
            ]
            return web.json_response(
                {
                    "data": data,
                    "message": "ok" if markets else "no markets found",
                    "summary": self._ai_context_engine.search_summary(
                        query,
                        markets,
                        language="en",
                    ),
                }
            )
        except asyncio.TimeoutError:
            cached = await self._cached_today_data(limit=20)
            matches = self._cached_search_results(cached, query, limit=5)
            logger.warning("Mini App search API timed out query=%s; returning cached fallback", query[:80])
            return web.json_response(
                {
                    "data": matches,
                    "message": (
                        "cached market matches"
                        if matches
                        else "Could not quickly find markets. Try another query."
                    ),
                    "summary": (
                        "Showing cached market matches while live search is slow."
                        if matches
                        else "Live search took too long and no cached match was found."
                    ),
                    "is_cached": bool(matches),
                    "fallback": True,
                    "error": not bool(matches),
                }
            )
        except Exception as exc:
            logger.warning("Mini App search API failed: %s", exc)
            return web.json_response(
                {
                    "data": [],
                    "message": "Could not quickly find markets. Try another query.",
                    "summary": "Search is temporarily unavailable.",
                    "error": True,
                }
            )
