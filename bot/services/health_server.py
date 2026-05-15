from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aiohttp import web
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.database.db import ping_database
from bot.database.repositories import get_latest_snapshots
from bot.services.market_analyzer import MarketAnalyzer, MarketMovement
from bot.services.market_health import calculate_market_health
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


def _market_to_api_object(market: Market, delta: float | None = None) -> dict[str, Any]:
    pulse = calculate_pulse_score(market, delta=delta)
    health = calculate_market_health(market)
    mood = calculate_market_mood(market, delta=delta, language="en")
    return {
        "market_id": market.id,
        "title": market.question,
        "probability": _percent(market.yes_probability),
        "probability_label": format_probability(market.yes_probability, "en"),
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
        "risk_flags": market_risk_flags(market, delta=delta),
        "url": market.url,
    }


def _today_item_to_api_object(item: TodayPulseItem) -> dict[str, Any]:
    result = _market_to_api_object(item.market, item.delta)
    result["why_it_matters"] = item.why_it_matters
    result["why_people_care"] = result["market_mood_reason"]
    return result


def _market_movement_to_api_object(item: MarketMovement) -> dict[str, Any]:
    return _market_to_api_object(item.market, item.delta)


def _smart_market_to_api_object(activity: MarketActivity) -> dict[str, Any]:
    return {
        "market_id": activity.market_id,
        "title": activity.market_title,
        "public_activity": round(activity.amount_usd, 2),
        "trades_count": activity.trades_count,
        "top_side": None,
        "url": "https://polymarket.com",
        "why_it_matters": "People are paying more attention to this market.",
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
        session_factory: async_sessionmaker[AsyncSession] | None = None,
    ) -> None:
        self._host = host
        self._port = port
        self._engine = engine
        self._market_analyzer = market_analyzer
        self._smart_money_analyzer = smart_money_analyzer
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
            return web.json_response(
                {"data": [_today_item_to_api_object(item) for item in items], "message": "ok"}
            )
        except Exception as exc:
            logger.warning("Mini App Today API failed: %s", exc)
            return self._api_empty("today pulse unavailable")

    async def _api_hot_markets(self, request: web.Request) -> web.Response:
        if self._market_analyzer is None:
            return self._api_empty("market analyzer unavailable")
        try:
            markets = await self._market_analyzer.get_hot_markets(limit=5)
            return web.json_response(
                {"data": [_market_to_api_object(market) for market in markets], "message": "ok"}
            )
        except Exception as exc:
            logger.warning("Mini App hot markets API failed: %s", exc)
            return self._api_empty("hot markets unavailable")

    async def _api_new_markets(self, request: web.Request) -> web.Response:
        if self._market_analyzer is None:
            return self._api_empty("market analyzer unavailable")
        try:
            markets = await self._market_analyzer.get_new_markets(limit=5)
            return web.json_response(
                {"data": [_market_to_api_object(market) for market in markets], "message": "ok"}
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
                    "data": [_market_movement_to_api_object(item) for item in movements[:5]],
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
            return web.json_response(
                {
                    "data": [_market_to_api_object(market) for market in markets],
                    "message": "ok" if markets else "no markets found",
                }
            )
        except Exception as exc:
            logger.warning("Mini App search API failed: %s", exc)
            return self._api_empty("search unavailable")
