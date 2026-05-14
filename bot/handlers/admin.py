from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.config import Settings
from bot.database.repositories import (
    count_alerts_sent_today,
    count_market_link_clicks,
    count_market_link_clicks_today,
    count_snapshots,
    count_topics,
    count_total_users,
    count_users_with_daily_digest,
    count_users_with_notifications,
    count_watchlist_items,
    get_latest_snapshots,
    get_recent_feedback,
    get_top_clicked_markets,
    get_top_search_queries,
)
from bot.services.market_analyzer import MarketAnalyzer
from bot.services.polymarket_client import PolymarketAPIError
from bot.services.today_pulse import build_today_pulse_items
from bot.utils.formatting import format_channel_digest
from bot.utils.logging import log_user_action

logger = logging.getLogger(__name__)
router = Router()


def format_whoami(telegram_user: object | None) -> str:
    if telegram_user is None:
        return "Не смог определить Telegram пользователя."

    username = getattr(telegram_user, "username", None)
    first_name = getattr(telegram_user, "first_name", None)
    return "\n".join(
        [
            "👤 Your Telegram ID:",
            str(getattr(telegram_user, "id", "unknown")),
            "",
            "Username:",
            f"@{username}" if username else "not set",
            "",
            "First name:",
            str(first_name or "not set"),
        ]
    )


def format_admin_stats(
    total_users: int,
    notifications_users: int,
    daily_digest_users: int,
    watchlist_items: int,
    topics_count: int,
    market_opens_today: int,
    market_opens_total: int,
    alerts_sent_today: int,
    snapshots_count: int,
    top_clicked_markets: list[tuple[str, str, int]],
    top_search_queries: list[tuple[str, int]],
) -> str:
    lines = [
        "📊 PulseMarket Admin Stats",
        "",
        f"Total users: {total_users}",
        f"Notifications enabled: {notifications_users}",
        f"Daily digest enabled: {daily_digest_users}",
        f"Watchlist items: {watchlist_items}",
        f"Topics count: {topics_count}",
        f"Market opens today: {market_opens_today}",
        f"Market opens total: {market_opens_total}",
        f"Alerts sent today: {alerts_sent_today}",
        f"Snapshots count: {snapshots_count}",
        "",
        "Top clicked markets:",
    ]
    if top_clicked_markets:
        lines.extend(
            f"{index}. {title[:80]} — {count}"
            for index, (_, title, count) in enumerate(top_clicked_markets, start=1)
        )
    else:
        lines.append("not tracked yet")

    lines.extend(["", "Top search queries:"])
    if top_search_queries:
        lines.extend(
            f"{index}. {query} — {count}"
            for index, (query, count) in enumerate(top_search_queries, start=1)
        )
    else:
        lines.append("not tracked yet")

    return "\n".join(lines)


def format_admin_feedback(feedback_items: list[object]) -> str:
    lines = ["📝 Recent feedback", ""]
    if not feedback_items:
        lines.append("No feedback yet.")
        return "\n".join(lines)

    for index, item in enumerate(feedback_items, start=1):
        username = getattr(item, "username", None)
        author = f"@{username}" if username else str(getattr(item, "telegram_user_id", "unknown"))
        message = str(getattr(item, "message", "")).strip().replace("\n", " ")
        lines.append(f"{index}. {author}: {message[:240]}")
    return "\n".join(lines)


@router.message(Command("whoami"))
async def whoami(message: Message) -> None:
    log_user_action(logger, message.from_user, "whoami")
    await message.answer(format_whoami(message.from_user))


@router.message(Command("admin_stats"))
async def admin_stats(
    message: Message,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    log_user_action(logger, message.from_user, "admin_stats")
    telegram_id = message.from_user.id if message.from_user else None
    if telegram_id not in settings.admin_telegram_ids:
        await message.answer("Команда доступна только администратору.")
        return

    async with session_factory() as session:
        stats = {
            "total_users": await count_total_users(session),
            "notifications_users": await count_users_with_notifications(session),
            "daily_digest_users": await count_users_with_daily_digest(session),
            "watchlist_items": await count_watchlist_items(session),
            "topics_count": await count_topics(session),
            "market_opens_today": await count_market_link_clicks_today(session),
            "market_opens_total": await count_market_link_clicks(session),
            "alerts_sent_today": await count_alerts_sent_today(session),
            "snapshots_count": await count_snapshots(session),
            "top_clicked_markets": await get_top_clicked_markets(session),
            "top_search_queries": await get_top_search_queries(session),
        }

    await message.answer(format_admin_stats(**stats))


@router.message(Command("admin_digest"))
async def admin_digest(
    message: Message,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
    market_analyzer: MarketAnalyzer,
) -> None:
    log_user_action(logger, message.from_user, "admin_digest")
    telegram_id = message.from_user.id if message.from_user else None
    if telegram_id not in settings.admin_telegram_ids:
        await message.answer("Команда доступна только администратору.")
        return

    try:
        hot_markets = await market_analyzer.get_hot_markets(limit=20)
        new_markets = await market_analyzer.get_new_markets(limit=20)
        markets = hot_markets + new_markets
        async with session_factory() as session:
            latest = await get_latest_snapshots(session, [market.id for market in markets])
        items = build_today_pulse_items(
            markets,
            latest_snapshots=latest,
            threshold=0.10,
            limit=3,
            language="en",
        )
    except PolymarketAPIError:
        logger.exception("Could not build admin digest")
        await message.answer("Could not load Polymarket data. Please try again later.")
        return
    except Exception:
        logger.exception("Could not build admin digest")
        await message.answer("Could not build digest. Please try again later.")
        return

    await message.answer(format_channel_digest(items, language="en"), disable_web_page_preview=True)


@router.message(Command("admin_feedback"))
async def admin_feedback(
    message: Message,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    log_user_action(logger, message.from_user, "admin_feedback")
    telegram_id = message.from_user.id if message.from_user else None
    if telegram_id not in settings.admin_telegram_ids:
        await message.answer("Команда доступна только администратору.")
        return

    async with session_factory() as session:
        feedback_items = await get_recent_feedback(session, limit=10)
    await message.answer(format_admin_feedback(feedback_items))
