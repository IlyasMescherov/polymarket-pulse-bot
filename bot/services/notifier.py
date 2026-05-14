from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.database.repositories import get_notification_users
from bot.keyboards.main import market_link_keyboard
from bot.services.ai_explainer import AIExplainer
from bot.services.market_analyzer import MarketAnalyzer
from bot.utils.formatting import format_movement_card

logger = logging.getLogger(__name__)


class Notifier:
    def __init__(
        self,
        bot: Bot,
        session_factory: async_sessionmaker[AsyncSession],
        market_analyzer: MarketAnalyzer,
        ai_explainer: AIExplainer,
    ) -> None:
        self._bot = bot
        self._session_factory = session_factory
        self._market_analyzer = market_analyzer
        self._ai_explainer = ai_explainer

    async def check_and_notify(self) -> None:
        async with self._session_factory() as session:
            users = await get_notification_users(session)

        threshold = min(
            (user.movement_threshold for user in users),
            default=0.10,
        )
        async with self._session_factory() as session:
            try:
                movements = await self._market_analyzer.detect_movements(
                    session,
                    threshold=threshold,
                )
            except Exception:
                await session.rollback()
                raise

        if not movements:
            logger.info("No sharp market movements detected")
            return

        if not users:
            logger.info("Sharp movements found, but no users have notifications enabled")
            return

        explanations = {}
        for movement in movements[:5]:
            explanations[movement.market.id] = await self._ai_explainer.explain_market(
                movement.market
            )

        for user in users:
            user_movements = [
                movement
                for movement in movements
                if abs(movement.delta) >= user.movement_threshold
            ][:5]
            for movement in user_movements:
                try:
                    await self._bot.send_message(
                        chat_id=user.telegram_id,
                        text=format_movement_card(
                            movement,
                            explanation=explanations.get(movement.market.id),
                        ),
                        reply_markup=market_link_keyboard(movement.market.url),
                        disable_web_page_preview=True,
                    )
                except TelegramAPIError as exc:
                    logger.warning(
                        "Could not send notification to user %s: %s",
                        user.telegram_id,
                        exc,
                    )
