from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.database.repositories import (
    alert_sent_recently,
    get_daily_digest_users,
    get_notification_users,
    get_recent_snapshots,
    get_user_topics,
    log_alert_sent,
)
from bot.keyboards.main import market_actions_keyboard
from bot.services.ai_explainer import AIExplainer
from bot.services.market_analyzer import MarketAnalyzer, market_matches_topics
from bot.services.pulse_score import calculate_pulse_score
from bot.services.risk_flags import count_strong_snapshot_moves, market_risk_flags
from bot.utils.formatting import format_movement_card, format_probability

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
            await self.send_daily_digests()
            return

        if not users:
            logger.info("Sharp movements found, but no users have notifications enabled")
            await self.send_daily_digests()
            return

        explanations = {}
        for movement in movements[:5]:
            explanations[movement.market.id] = await self._ai_explainer.explain_market(
                movement.market
            )

        for user in users:
            async with self._session_factory() as session:
                topics = [topic.topic for topic in await get_user_topics(session, user.telegram_id)]
                user_movements = []
                for movement in movements:
                    if abs(movement.delta) < user.movement_threshold:
                        continue
                    if (movement.market.volume or 0) < user.min_volume_for_alerts:
                        continue
                    if not market_matches_topics(movement.market, topics):
                        continue
                    if await alert_sent_recently(
                        session,
                        user.telegram_id,
                        movement.market.id,
                        "sharp_move",
                    ):
                        continue
                    user_movements.append(movement)
                    await log_alert_sent(
                        session,
                        user.telegram_id,
                        movement.market.id,
                        "sharp_move",
                    )
                    if len(user_movements) >= 5:
                        break
                await session.commit()

            for movement in user_movements:
                pulse_score = calculate_pulse_score(movement.market, delta=movement.delta)
                async with self._session_factory() as session:
                    recent = await get_recent_snapshots(session, movement.market.id, limit=8)
                risk_flags = market_risk_flags(
                    movement.market,
                    delta=movement.delta,
                    threshold=user.movement_threshold,
                    strong_moves_count=count_strong_snapshot_moves(
                        recent,
                        user.movement_threshold,
                    ),
                )
                try:
                    await self._bot.send_message(
                        chat_id=user.telegram_id,
                        text=format_movement_card(
                            movement,
                            explanation=explanations.get(movement.market.id),
                            pulse_score=pulse_score,
                            risk_flags=risk_flags,
                        ),
                        reply_markup=market_actions_keyboard(
                            movement.market.url,
                            movement.market.id,
                            user.language,
                        ),
                        disable_web_page_preview=True,
                    )
                except TelegramAPIError as exc:
                    logger.warning(
                        "Could not send notification to user %s: %s",
                        user.telegram_id,
                        exc,
                    )

        await self.send_daily_digests()

    async def send_daily_digests(self) -> None:
        async with self._session_factory() as session:
            users = await get_daily_digest_users(session)
        if not users:
            return

        try:
            markets = await self._market_analyzer.get_hot_markets(limit=30)
        except Exception:
            logger.exception("Could not build daily digest")
            return

        for user in users:
            async with self._session_factory() as session:
                if await alert_sent_recently(
                    session,
                    user.telegram_id,
                    "daily_digest",
                    "daily_digest",
                    cooldown_hours=20,
                ):
                    continue
                topics = [topic.topic for topic in await get_user_topics(session, user.telegram_id)]
                selected = [
                    market
                    for market in markets
                    if market_matches_topics(market, topics)
                ][:3]
                if not selected:
                    selected = markets[:3]
                await log_alert_sent(
                    session,
                    user.telegram_id,
                    "daily_digest",
                    "daily_digest",
                )
                await session.commit()

            lines = ["📰 PulseMarket Daily Digest", "", "Сегодня главное:"]
            for index, market in enumerate(selected, start=1):
                pulse_score = calculate_pulse_score(market)
                lines.extend(
                    [
                        "",
                        f"{index}. {market.question}",
                        f"Вероятность: {format_probability(market.yes_probability)}",
                        "Движение: данных пока нет",
                        f"Pulse Score: {pulse_score.value}/100",
                    ]
                )
            try:
                await self._bot.send_message(
                    chat_id=user.telegram_id,
                    text="\n".join(lines),
                    disable_web_page_preview=True,
                )
            except TelegramAPIError as exc:
                logger.warning(
                    "Could not send daily digest to user %s: %s",
                    user.telegram_id,
                    exc,
                )
