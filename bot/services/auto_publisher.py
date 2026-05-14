from __future__ import annotations

import logging
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from bot.config import Settings
from bot.services.channel_publisher import ChannelPublisher
from bot.services.content_publisher import ContentPublisher
from bot.services.x_publisher import XPublisher

logger = logging.getLogger(__name__)


def parse_publish_time(value: str) -> time:
    try:
        hour_text, minute_text = value.strip().split(":", maxsplit=1)
        hour = int(hour_text)
        minute = int(minute_text)
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return time(hour=hour, minute=minute)
    except (AttributeError, TypeError, ValueError):
        pass
    logger.warning("Invalid AUTO_CHANNEL_POSTING_TIME; falling back to 09:00")
    return time(hour=9, minute=0)


def parse_timezone(value: str) -> ZoneInfo:
    try:
        return ZoneInfo(value.strip() or "UTC")
    except (AttributeError, ZoneInfoNotFoundError):
        logger.warning("Invalid AUTO_CHANNEL_POSTING_TIMEZONE; falling back to UTC")
        return ZoneInfo("UTC")


class DailyPublishingJob:
    def __init__(
        self,
        content_publisher: ContentPublisher,
        channel_publisher: ChannelPublisher,
        x_publisher: XPublisher,
        settings: Settings,
        interval_seconds: int = 900,
    ) -> None:
        self._content_publisher = content_publisher
        self._channel_publisher = channel_publisher
        self._x_publisher = x_publisher
        self._settings = settings
        self._interval_seconds = interval_seconds
        self._last_run_date: str | None = None

    def _is_due(self, now: datetime | None = None) -> bool:
        timezone_info = parse_timezone(self._settings.auto_channel_posting_timezone)
        current = (now or datetime.now(timezone.utc)).astimezone(timezone_info)
        schedule_time = parse_publish_time(self._settings.auto_channel_posting_time)
        scheduled = current.replace(
            hour=schedule_time.hour,
            minute=schedule_time.minute,
            second=0,
            microsecond=0,
        )
        seconds_since = (current - scheduled).total_seconds()
        window_seconds = max(60, self._interval_seconds + 60)
        return 0 <= seconds_since <= window_seconds

    async def run_due(self, now: datetime | None = None) -> None:
        timezone_info = parse_timezone(self._settings.auto_channel_posting_timezone)
        current = (now or datetime.now(timezone.utc)).astimezone(timezone_info)
        run_key = current.date().isoformat()
        if self._last_run_date == run_key or not self._is_due(current):
            return

        self._last_run_date = run_key
        channel_text = await self._content_publisher.generate_today_pulse_channel_post("en")
        if not channel_text:
            logger.info("Daily publishing skipped: empty Today’s Pulse post")
            return

        if self._settings.auto_channel_posting_enabled:
            result = await self._channel_publisher.publish_to_telegram_channel(
                channel_text,
                post_type="today_pulse",
            )
            logger.info("Daily channel publish result: %s", result.status)

        if self._settings.x_drafts_enabled:
            x_text = await self._content_publisher.generate_x_today_pulse_draft("en")
            if x_text:
                result = await self._x_publisher.create_x_draft(
                    x_text,
                    post_type="today_pulse",
                )
                logger.info("Daily X draft result: %s", result.status)
