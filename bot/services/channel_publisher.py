from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from aiogram import Bot
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.config import Settings
from bot.database.repositories import (
    content_hash_exists,
    create_published_post,
    has_recent_published_post,
)
from bot.services.content_publisher import content_hash

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class PublishResult:
    platform: str
    post_type: str
    status: str
    content_hash: str
    message: str
    published: bool = False


class ChannelPublisher:
    def __init__(
        self,
        bot: Bot,
        session_factory: async_sessionmaker[AsyncSession],
        settings: Settings,
    ) -> None:
        self._bot = bot
        self._session_factory = session_factory
        self._settings = settings

    @property
    def channel_id(self) -> str | None:
        return self._settings.project_channel_id

    async def publish_to_telegram_channel(
        self,
        text: str,
        post_type: str = "today_pulse",
        bypass_enabled: bool = False,
    ) -> PublishResult:
        normalized_text = text.strip()
        digest = content_hash(normalized_text)
        platform = "telegram_channel"

        if not normalized_text:
            return PublishResult(platform, post_type, "skipped", digest, "Post text is empty")
        if not self._settings.project_channel_id:
            return PublishResult(platform, post_type, "skipped", digest, "PROJECT_CHANNEL_ID is not set")
        if not bypass_enabled and not self._settings.auto_channel_posting_enabled:
            return PublishResult(platform, post_type, "skipped", digest, "Automatic channel posting is disabled")

        async with self._session_factory() as session:
            if await content_hash_exists(session, platform, digest):
                return PublishResult(platform, post_type, "skipped", digest, "Duplicate content skipped")
            if await has_recent_published_post(
                session,
                platform,
                post_type,
                self._settings.auto_channel_posting_min_hours_between_posts,
            ):
                return PublishResult(platform, post_type, "skipped", digest, "Cooldown is still active")

            try:
                await self._bot.send_message(
                    self._settings.project_channel_id,
                    normalized_text,
                    disable_web_page_preview=True,
                )
            except Exception as exc:
                logger.exception("Telegram channel publish failed")
                await create_published_post(
                    session,
                    platform=platform,
                    post_type=post_type,
                    content_hash=digest,
                    content_text=normalized_text,
                    status="failed",
                    error_message=type(exc).__name__,
                )
                await session.commit()
                return PublishResult(platform, post_type, "failed", digest, "Telegram publish failed")

            try:
                await create_published_post(
                    session,
                    platform=platform,
                    post_type=post_type,
                    content_hash=digest,
                    content_text=normalized_text,
                    status="published",
                    published_at=datetime.now(timezone.utc),
                )
                await session.commit()
            except IntegrityError:
                await session.rollback()
                return PublishResult(platform, post_type, "skipped", digest, "Duplicate content skipped")

        logger.info(
            "published_post platform=%s post_type=%s status=published hash=%s",
            platform,
            post_type,
            digest[:12],
        )
        return PublishResult(platform, post_type, "published", digest, "Published to Telegram channel", True)


async def check_channel_access(bot: Bot, channel_id: str | None) -> tuple[bool, str]:
    if not channel_id:
        return False, "PROJECT_CHANNEL_ID is not set."
    try:
        chat: Any = await bot.get_chat(channel_id)
    except Exception as exc:
        logger.warning("Channel access check failed: %s", type(exc).__name__)
        return False, "Could not access the channel. Make sure the bot is an admin."

    title = getattr(chat, "title", None) or getattr(chat, "username", None) or channel_id
    return True, f"Channel access OK: {title}"
