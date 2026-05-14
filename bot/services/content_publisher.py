from __future__ import annotations

import hashlib
import logging
from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.database.repositories import get_latest_snapshots
from bot.services.market_analyzer import MarketAnalyzer
from bot.services.polymarket_client import PolymarketAPIError
from bot.services.smart_money_analyzer import MarketActivity, SmartMoneyAnalyzer
from bot.services.today_pulse import TodayPulseItem, build_today_pulse_items
from bot.utils.formatting import format_compact_usd, format_probability

logger = logging.getLogger(__name__)

DEFAULT_BOT_HANDLE = "@PulseMarketAIBot"


def content_hash(text: str) -> str:
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()


def _title(text: str, limit: int = 100) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 1].rstrip() + "…"


def format_today_pulse_channel_post(
    items: Sequence[TodayPulseItem],
    bot_handle: str = DEFAULT_BOT_HANDLE,
) -> str | None:
    if not items:
        return None

    lines = [
        "📰 Today’s Pulse",
        "",
        f"{min(len(items), 3)} Polymarket markets worth watching today:",
        "",
    ]
    for index, item in enumerate(items[:3], start=1):
        lines.extend(
            [
                f"{index}. {_title(item.market.question)}",
                f"Probability: {format_probability(item.market.yes_probability, 'en')}",
                f"Pulse Score: {item.pulse_score.value}/100",
                f"Why it matters: {item.why_it_matters}",
                "",
            ]
        )

    lines.extend(
        [
            "Research only.",
            "No trading. No wallets. No financial advice.",
            "",
            "Bot:",
            bot_handle,
        ]
    )
    return "\n".join(lines).strip()


def format_smart_money_channel_post(
    activities: Sequence[MarketActivity],
    bot_handle: str = DEFAULT_BOT_HANDLE,
) -> str | None:
    if not activities:
        return None

    lines = [
        "🧠 Smart Money Radar",
        "",
        "Unusual public activity worth watching:",
        "",
    ]
    for index, activity in enumerate(activities[:3], start=1):
        lines.extend(
            [
                f"{index}. {_title(activity.market_title)}",
                f"Public activity: {format_compact_usd(activity.amount_usd, 'en')}",
                "Why it matters: Active public activity can show where market attention is moving.",
                "",
            ]
        )

    lines.extend(
        [
            "Research only.",
            "No trading. No wallets. No copy trading. No financial advice.",
            "",
            "Bot:",
            bot_handle,
        ]
    )
    return "\n".join(lines).strip()


def format_x_today_pulse_draft(
    items: Sequence[TodayPulseItem],
    bot_handle: str = DEFAULT_BOT_HANDLE,
) -> str | None:
    if not items:
        return None

    for count in (2, 1):
        lines = ["📰 Today’s Pulse", ""]
        for index, item in enumerate(items[:count], start=1):
            lines.append(
                f"{index}) {_title(item.market.question, 54)} · "
                f"{format_probability(item.market.yes_probability, 'en')} · "
                f"Pulse {item.pulse_score.value}/100"
            )
        lines.extend(
            [
                "",
                "Research only. No trading. No financial advice.",
                "",
                bot_handle,
            ]
        )
        draft = "\n".join(lines).strip()
        if len(draft) <= 280:
            return draft

    item = items[0]
    fallback = (
        "📰 Today’s Pulse\n\n"
        f"{_title(item.market.question, 72)} · "
        f"{format_probability(item.market.yes_probability, 'en')} · "
        f"Pulse {item.pulse_score.value}/100\n\n"
        "Research only. No trading. No financial advice.\n\n"
        f"{bot_handle}"
    )
    return fallback[:277].rstrip() + "..." if len(fallback) > 280 else fallback


class ContentPublisher:
    def __init__(
        self,
        market_analyzer: MarketAnalyzer,
        smart_money_analyzer: SmartMoneyAnalyzer,
        session_factory: async_sessionmaker[AsyncSession],
        bot_handle: str = DEFAULT_BOT_HANDLE,
    ) -> None:
        self._market_analyzer = market_analyzer
        self._smart_money_analyzer = smart_money_analyzer
        self._session_factory = session_factory
        self._bot_handle = bot_handle or DEFAULT_BOT_HANDLE

    async def _today_items(self, limit: int = 3) -> list[TodayPulseItem]:
        hot_markets = await self._market_analyzer.get_hot_markets(limit=20)
        new_markets = await self._market_analyzer.get_new_markets(limit=20)
        markets = hot_markets + new_markets
        if not markets:
            return []

        async with self._session_factory() as session:
            latest = await get_latest_snapshots(session, [market.id for market in markets])
        return build_today_pulse_items(
            markets,
            latest_snapshots=latest,
            threshold=0.10,
            limit=limit,
            language="en",
        )

    async def generate_today_pulse_channel_post(self, lang: str = "en") -> str | None:
        if lang != "en":
            logger.info("Channel publishing is English-first; ignoring lang=%s", lang)
        try:
            items = await self._today_items(limit=3)
        except PolymarketAPIError:
            logger.exception("Could not generate Today’s Pulse channel post")
            return None
        return format_today_pulse_channel_post(items, bot_handle=self._bot_handle)

    async def generate_smart_money_channel_post(self, lang: str = "en") -> str | None:
        if lang != "en":
            logger.info("Channel publishing is English-first; ignoring lang=%s", lang)
        try:
            activities = await self._smart_money_analyzer.active_markets(limit=3)
        except Exception:
            logger.exception("Could not generate Smart Money channel post")
            return None
        return format_smart_money_channel_post(activities, bot_handle=self._bot_handle)

    async def generate_x_today_pulse_draft(self, lang: str = "en") -> str | None:
        if lang != "en":
            logger.info("X draft publishing is English-first; ignoring lang=%s", lang)
        try:
            items = await self._today_items(limit=3)
        except PolymarketAPIError:
            logger.exception("Could not generate X Today’s Pulse draft")
            return None
        return format_x_today_pulse_draft(items, bot_handle=self._bot_handle)
