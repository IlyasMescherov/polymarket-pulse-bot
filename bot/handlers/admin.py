from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.config import Settings
from bot.database.repositories import (
    count_alerts_sent_today,
    count_market_link_clicks,
    count_market_link_clicks_today,
    count_large_trades_detected_today,
    count_snapshots,
    count_smart_money_alerts_today,
    count_smart_money_snapshots,
    count_topics,
    count_total_users,
    count_tracked_traders,
    count_users_with_daily_digest,
    count_users_with_notifications,
    count_watchlist_items,
    get_latest_snapshots,
    get_recent_feedback,
    get_recent_smart_money_snapshots,
    get_top_clicked_markets,
    get_top_search_queries,
)
from bot.services.market_analyzer import MarketAnalyzer
from bot.services.channel_publisher import ChannelPublisher, check_channel_access
from bot.services.content_publisher import ContentPublisher
from bot.services.polymarket_client import PolymarketAPIError
from bot.services.today_pulse import build_today_pulse_items
from bot.services.x_publisher import XPublisher
from bot.utils.formatting import format_channel_digest
from bot.utils.logging import log_user_action

logger = logging.getLogger(__name__)
router = Router()

ADMIN_PUBLISH_CHANNEL = "admin:publish_today:channel"
ADMIN_PUBLISH_X_DRAFT = "admin:publish_today:x_draft"
ADMIN_PUBLISH_CANCEL = "admin:publish_today:cancel"


def _is_admin(settings: Settings, telegram_user: object | None) -> bool:
    telegram_id = getattr(telegram_user, "id", None)
    return telegram_id in settings.admin_telegram_ids


def _admin_publish_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Publish to channel",
                    callback_data=ADMIN_PUBLISH_CHANNEL,
                )
            ],
            [
                InlineKeyboardButton(
                    text="Generate X draft",
                    callback_data=ADMIN_PUBLISH_X_DRAFT,
                )
            ],
            [InlineKeyboardButton(text="Cancel", callback_data=ADMIN_PUBLISH_CANCEL)],
        ]
    )


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
    smart_money_snapshots_count: int = 0,
    tracked_wallets_count: int = 0,
    smart_money_alerts_today: int = 0,
    large_trades_detected_today: int = 0,
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
        f"Smart Money snapshots count: {smart_money_snapshots_count}",
        f"Tracked wallets count: {tracked_wallets_count}",
        f"Smart Money alerts sent today: {smart_money_alerts_today}",
        f"Large public activities detected today: {large_trades_detected_today}",
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


def format_smart_money_digest_block(snapshots: list[object]) -> str:
    if not snapshots:
        return ""

    lines = ["", "🧠 Smart Money Radar", ""]
    for index, item in enumerate(snapshots[:3], start=1):
        title = str(getattr(item, "market_title", "") or "Public activity")
        amount = getattr(item, "amount_usd", None)
        amount_text = f" · {amount:,.0f} USD public activity" if amount else ""
        lines.append(f"{index}. {title[:100]}{amount_text}")
    lines.extend(
        [
            "",
            "Research only.",
            "No copy trading. No trade execution.",
        ]
    )
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
    if not _is_admin(settings, message.from_user):
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
            "smart_money_snapshots_count": await count_smart_money_snapshots(session),
            "tracked_wallets_count": await count_tracked_traders(session),
            "smart_money_alerts_today": await count_smart_money_alerts_today(session),
            "large_trades_detected_today": await count_large_trades_detected_today(session),
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
    if not _is_admin(settings, message.from_user):
        await message.answer("Команда доступна только администратору.")
        return

    try:
        hot_markets = await market_analyzer.get_hot_markets(limit=20)
        new_markets = await market_analyzer.get_new_markets(limit=20)
        markets = hot_markets + new_markets
        async with session_factory() as session:
            latest = await get_latest_snapshots(session, [market.id for market in markets])
            smart_money_snapshots = await get_recent_smart_money_snapshots(session, limit=3)
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

    digest = format_channel_digest(items, language="en")
    smart_money_block = format_smart_money_digest_block(smart_money_snapshots)
    await message.answer(
        digest + smart_money_block,
        disable_web_page_preview=True,
    )


@router.message(Command("admin_feedback"))
async def admin_feedback(
    message: Message,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    log_user_action(logger, message.from_user, "admin_feedback")
    if not _is_admin(settings, message.from_user):
        await message.answer("Команда доступна только администратору.")
        return

    async with session_factory() as session:
        feedback_items = await get_recent_feedback(session, limit=10)
    await message.answer(format_admin_feedback(feedback_items))


@router.message(Command("admin_check_channel"))
async def admin_check_channel(
    message: Message,
    settings: Settings,
    bot: Bot,
) -> None:
    log_user_action(logger, message.from_user, "admin_check_channel")
    if not _is_admin(settings, message.from_user):
        await message.answer("Команда доступна только администратору.")
        return

    ok, text = await check_channel_access(bot, settings.project_channel_id)
    prefix = "✅" if ok else "⚠️"
    await message.answer(f"{prefix} {text}")


@router.message(Command("admin_publish_today"))
async def admin_publish_today(
    message: Message,
    settings: Settings,
    content_publisher: ContentPublisher,
) -> None:
    log_user_action(logger, message.from_user, "admin_publish_today")
    if not _is_admin(settings, message.from_user):
        await message.answer("Команда доступна только администратору.")
        return

    text = await content_publisher.generate_today_pulse_channel_post("en")
    if not text:
        await message.answer("Could not generate Today’s Pulse preview right now.")
        return

    await message.answer(
        "Preview:\n\n" + text,
        reply_markup=_admin_publish_keyboard(),
        disable_web_page_preview=True,
    )


@router.message(Command("admin_x_draft"))
async def admin_x_draft(
    message: Message,
    settings: Settings,
    content_publisher: ContentPublisher,
    x_publisher: XPublisher,
) -> None:
    log_user_action(logger, message.from_user, "admin_x_draft")
    if not _is_admin(settings, message.from_user):
        await message.answer("Команда доступна только администратору.")
        return

    text = await content_publisher.generate_x_today_pulse_draft("en")
    if not text:
        await message.answer("Could not generate X draft right now.")
        return
    result = await x_publisher.create_x_draft(text, post_type="today_pulse")
    await message.answer(f"X draft status: {result.status}. {result.message}")


@router.callback_query(F.data == ADMIN_PUBLISH_CHANNEL)
async def admin_publish_today_channel_callback(
    callback: CallbackQuery,
    settings: Settings,
    content_publisher: ContentPublisher,
    channel_publisher: ChannelPublisher,
) -> None:
    if not _is_admin(settings, callback.from_user):
        await callback.answer("Admin only", show_alert=True)
        return
    await callback.answer("Publishing preview")
    text = await content_publisher.generate_today_pulse_channel_post("en")
    if not text or not callback.message:
        return
    result = await channel_publisher.publish_to_telegram_channel(
        text,
        post_type="today_pulse",
        bypass_enabled=True,
    )
    await callback.message.answer(f"Telegram channel status: {result.status}. {result.message}")


@router.callback_query(F.data == ADMIN_PUBLISH_X_DRAFT)
async def admin_publish_today_x_callback(
    callback: CallbackQuery,
    settings: Settings,
    content_publisher: ContentPublisher,
    x_publisher: XPublisher,
) -> None:
    if not _is_admin(settings, callback.from_user):
        await callback.answer("Admin only", show_alert=True)
        return
    await callback.answer("Generating X draft")
    text = await content_publisher.generate_x_today_pulse_draft("en")
    if not text or not callback.message:
        return
    result = await x_publisher.create_x_draft(text, post_type="today_pulse")
    await callback.message.answer(f"X draft status: {result.status}. {result.message}")


@router.callback_query(F.data == ADMIN_PUBLISH_CANCEL)
async def admin_publish_cancel_callback(callback: CallbackQuery, settings: Settings) -> None:
    if not _is_admin(settings, callback.from_user):
        await callback.answer("Admin only", show_alert=True)
        return
    await callback.answer("Cancelled")
    if callback.message:
        await callback.message.answer("Publishing cancelled.")
