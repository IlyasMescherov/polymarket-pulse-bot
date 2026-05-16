from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aiohttp import web
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.database.db import ping_database
from bot.database.repositories import get_latest_snapshots, get_recent_snapshots
from bot.services.ai_context_engine import AIContextEngine, MarketContext
from bot.services.ai_insight_engine import generate_market_briefing
from bot.services.event_categories import category_label, classify_market_category
from bot.services.market_analyzer import MarketAnalyzer, MarketMovement
from bot.services.market_health import calculate_market_health
from bot.services.market_indicators import calculate_market_indicators
from bot.services.market_mood import calculate_market_mood
from bot.services.polymarket_client import Market
from bot.services.pulse_score import calculate_pulse_score
from bot.services.risk_flags import market_risk_flags
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
    category = context.category if context is not None else classify_market_category(market)
    return {
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
        **indicators.as_dict(),
        "risk_flags": market_risk_flags(market, delta=delta),
        "url": market.url,
    }


def _category_from_title(title: str) -> str:
    text = title.lower()
    if any(word in text for word in ("bitcoin", "btc", "ethereum", "crypto", "binance")):
        return "crypto"
    if any(word in text for word in ("iran", "israel", "trump", "election", "president", "war", "diplomacy")):
        return "politics"
    if any(word in text for word in ("nba", "nfl", "ufc", "soccer", "football", "tennis", "match", "playoff")):
        return "sports"
    if any(word in text for word in ("openai", "nvidia", "anthropic", " ai ")):
        return "ai"
    return "global"


def _attention_reason_for_title(title: str) -> str:
    category = _category_from_title(title)
    return {
        "crypto": "Crypto volatility made this market more visible.",
        "politics": "Political headlines made this market more visible.",
        "sports": "Event timing made this market more visible.",
        "ai": "AI news flow made this topic more visible today.",
        "global": "This market became more visible in the public activity layer.",
    }[category]


def _today_item_to_api_object(item: TodayPulseItem) -> dict[str, Any]:
    result = _market_to_api_object(item.market, item.delta)
    result["why_it_matters"] = item.why_it_matters
    result["why_people_care"] = result["market_mood_reason"]
    return result


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
        **indicators.as_dict(),
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
        session_factory: async_sessionmaker[AsyncSession] | None = None,
    ) -> None:
        self._host = host
        self._port = port
        self._engine = engine
        self._market_analyzer = market_analyzer
        self._smart_money_analyzer = smart_money_analyzer
        self._ai_context_engine = ai_context_engine or AIContextEngine(None)
        self._session_factory = session_factory
        self._runner: web.AppRunner | None = None

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

    async def stop(self) -> None:
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

    async def _market_history(self, market_id: str) -> list[Any]:
        if self._session_factory is None:
            return []
        try:
            async with self._session_factory() as session:
                return await get_recent_snapshots(session, market_id, limit=48)
        except Exception as exc:
            logger.debug("Could not load market memory for %s: %s", market_id, exc)
            return []

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
        result["why_it_matters"] = context.why_people_care
        return result

    async def _today_api_payload(self, items: list[TodayPulseItem]) -> dict[str, Any]:
        data: list[dict[str, Any]] = []
        contexts: list[MarketContext] = []
        for item in items:
            pulse = item.pulse_score
            mood = calculate_market_mood(item.market, delta=item.delta, language="en")
            context = await self._ai_context_engine.market_context(
                item.market,
                pulse,
                mood,
                delta=item.delta,
                language="en",
                history=await self._market_history(item.market.id),
            )
            contexts.append(context)
            result = _market_to_api_object(item.market, item.delta, context=context)
            result["why_it_matters"] = context.why_people_care
            data.append(result)

        narrative = await self._ai_context_engine.daily_narrative(
            [item.market for item in items],
            contexts,
            language="en",
        )
        return {
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
        }

    async def _api_today(self, request: web.Request) -> web.Response:
        if self._market_analyzer is None:
            return self._api_empty("market analyzer unavailable")
        try:
            hot_markets = await self._market_analyzer.get_hot_markets(limit=20)
            new_markets = await self._market_analyzer.get_new_markets(limit=10)
            markets = [*hot_markets, *new_markets]
            latest = {}
            if self._session_factory is not None and markets:
                async with self._session_factory() as session:
                    latest = await get_latest_snapshots(session, [market.id for market in markets])
            items = build_today_pulse_items(
                markets,
                latest_snapshots=latest,
                limit=5,
                language="en",
            )
            return web.json_response(await self._today_api_payload(items))
        except Exception as exc:
            logger.warning("Mini App Today API failed: %s", exc)
            return self._api_empty("today pulse unavailable")

    async def _api_hot_markets(self, request: web.Request) -> web.Response:
        if self._market_analyzer is None:
            return self._api_empty("market analyzer unavailable")
        try:
            markets = await self._market_analyzer.get_hot_markets(limit=5)
            data = [await self._market_api_object(market) for market in markets]
            return web.json_response(
                {"data": data, "message": "ok"}
            )
        except Exception as exc:
            logger.warning("Mini App hot markets API failed: %s", exc)
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
            markets = await self._market_analyzer.search_markets(query, limit=5)
            data = [await self._market_api_object(market) for market in markets]
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
        except Exception as exc:
            logger.warning("Mini App search API failed: %s", exc)
            return self._api_empty("search unavailable")
