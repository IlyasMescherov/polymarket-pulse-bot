from __future__ import annotations

import logging
from dataclasses import dataclass

from aiogram import Bot
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.config import Settings
from bot.database.repositories import content_hash_exists, create_published_post
from bot.services.content_publisher import content_hash

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class XDraftResult:
    status: str
    content_hash: str
    message: str
    draft_created: bool = False


class XPublisher:
    def __init__(
        self,
        bot: Bot,
        session_factory: async_sessionmaker[AsyncSession],
        settings: Settings,
    ) -> None:
        self._bot = bot
        self._session_factory = session_factory
        self._settings = settings

    def _draft_mode_enabled(self) -> bool:
        return self._settings.x_drafts_enabled or self._settings.x_posting_mode == "draft"

    async def _notify_admins(self, text: str) -> None:
        for telegram_id in self._settings.admin_telegram_ids:
            try:
                await self._bot.send_message(
                    telegram_id,
                    text,
                    disable_web_page_preview=True,
                )
            except Exception:
                logger.warning("Could not send X draft to admin_id=%s", telegram_id)

    async def create_x_draft(
        self,
        text: str,
        post_type: str = "today_pulse",
        notify_admins: bool = True,
    ) -> XDraftResult:
        normalized_text = text.strip()
        digest = content_hash(normalized_text)
        platform = "x_draft"
        if not normalized_text:
            return XDraftResult("skipped", digest, "Draft text is empty")

        if self._settings.auto_x_posting_enabled and self._settings.x_posting_mode == "api":
            missing = [
                name
                for name, value in (
                    ("X_API_KEY", self._settings.x_api_key),
                    ("X_API_SECRET", self._settings.x_api_secret),
                    ("X_ACCESS_TOKEN", self._settings.x_access_token),
                    ("X_ACCESS_TOKEN_SECRET", self._settings.x_access_token_secret),
                )
                if not value
            ]
            if missing:
                await self._notify_admins(
                    "🐦 X API posting is not active because credentials are incomplete. "
                    "Draft mode is safer for now."
                )
            logger.info("X API posting requested but not implemented; using draft structure")

        if not self._draft_mode_enabled():
            return XDraftResult("skipped", digest, "X draft mode is disabled")

        async with self._session_factory() as session:
            if await content_hash_exists(session, platform, digest):
                return XDraftResult("skipped", digest, "Duplicate X draft skipped")
            try:
                await create_published_post(
                    session,
                    platform=platform,
                    post_type=post_type,
                    content_hash=digest,
                    content_text=normalized_text,
                    status="draft",
                )
                await session.commit()
            except IntegrityError:
                await session.rollback()
                return XDraftResult("skipped", digest, "Duplicate X draft skipped")

        if notify_admins:
            await self._notify_admins(
                "\n".join(
                    [
                        "🐦 X draft ready",
                        "",
                        normalized_text,
                        "",
                        "Copy and publish manually.",
                    ]
                )
            )
        logger.info("published_post platform=x_draft post_type=%s status=draft hash=%s", post_type, digest[:12])
        return XDraftResult("draft", digest, "X draft created", True)
