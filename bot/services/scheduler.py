from __future__ import annotations

import asyncio
import logging

from bot.services.auto_publisher import DailyPublishingJob
from bot.services.news_intelligence_engine import NewsRefreshJob
from bot.services.notifier import Notifier

logger = logging.getLogger(__name__)


class Scheduler:
    def __init__(
        self,
        notifier: Notifier,
        interval_seconds: int = 900,
        daily_publishing_job: DailyPublishingJob | None = None,
        news_refresh_job: NewsRefreshJob | None = None,
    ) -> None:
        self._notifier = notifier
        self._interval_seconds = interval_seconds
        self._daily_publishing_job = daily_publishing_job
        self._news_refresh_job = news_refresh_job

    async def run(self) -> None:
        logger.info("Scheduler started with %s seconds interval", self._interval_seconds)
        await asyncio.sleep(5)
        while True:
            try:
                await self._notifier.check_and_notify()
                if self._daily_publishing_job is not None:
                    await self._daily_publishing_job.run_due()
                if self._news_refresh_job is not None:
                    await self._news_refresh_job.run_due()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Scheduled job failed")

            await asyncio.sleep(self._interval_seconds)
