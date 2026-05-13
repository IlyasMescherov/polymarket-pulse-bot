from __future__ import annotations

import asyncio
import logging

from bot.services.notifier import Notifier

logger = logging.getLogger(__name__)


class Scheduler:
    def __init__(self, notifier: Notifier, interval_seconds: int = 900) -> None:
        self._notifier = notifier
        self._interval_seconds = interval_seconds

    async def run(self) -> None:
        logger.info("Scheduler started with %s seconds interval", self._interval_seconds)
        await asyncio.sleep(5)
        while True:
            try:
                await self._notifier.check_and_notify()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Scheduled notification check failed")

            await asyncio.sleep(self._interval_seconds)

