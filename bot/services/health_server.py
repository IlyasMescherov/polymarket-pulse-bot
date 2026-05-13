from __future__ import annotations

import logging
from datetime import datetime, timezone

from aiohttp import web
from sqlalchemy.ext.asyncio import AsyncEngine

from bot.database.db import ping_database

logger = logging.getLogger(__name__)


class HealthServer:
    def __init__(self, host: str, port: int, engine: AsyncEngine) -> None:
        self._host = host
        self._port = port
        self._engine = engine
        self._runner: web.AppRunner | None = None

    async def start(self) -> None:
        app = web.Application()
        app.router.add_get("/health", self._health)

        self._runner = web.AppRunner(app)
        await self._runner.setup()
        site = web.TCPSite(self._runner, host=self._host, port=self._port)
        await site.start()
        logger.info("Health endpoint started on %s:%s", self._host, self._port)

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
