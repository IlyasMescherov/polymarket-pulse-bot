from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import MarketSnapshot, User, UserAlertLog, UserTopic, UserWatchlist
from bot.services.polymarket_client import Market


ALLOWED_LANGUAGES = {"ru", "en"}
ALLOWED_MOVEMENT_THRESHOLDS = {0.05, 0.10, 0.15, 0.20}
ALLOWED_MIN_ALERT_VOLUMES = {0.0, 10_000.0, 50_000.0, 100_000.0}


def _full_name(telegram_user: Any) -> str | None:
    parts = [
        getattr(telegram_user, "first_name", None),
        getattr(telegram_user, "last_name", None),
    ]
    name = " ".join(part for part in parts if part)
    return name or None


async def upsert_user(session: AsyncSession, telegram_user: Any) -> User:
    telegram_id = getattr(telegram_user, "id", None)
    if telegram_id is None:
        raise ValueError("Telegram user id is required")

    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(
            telegram_id=telegram_id,
            username=getattr(telegram_user, "username", None),
            full_name=_full_name(telegram_user),
        )
        session.add(user)
    else:
        user.username = getattr(telegram_user, "username", None)
        user.full_name = _full_name(telegram_user)

    await session.flush()
    return user


async def set_notifications(
    session: AsyncSession,
    telegram_user: Any,
    enabled: bool,
) -> User:
    user = await upsert_user(session, telegram_user)
    user.notifications_enabled = enabled
    await session.flush()
    return user


async def set_daily_digest(
    session: AsyncSession,
    telegram_user: Any,
    enabled: bool,
) -> User:
    user = await upsert_user(session, telegram_user)
    user.daily_digest_enabled = enabled
    await session.flush()
    return user


async def set_language(
    session: AsyncSession,
    telegram_user: Any,
    language: str,
) -> User:
    normalized = language.lower()
    if normalized not in ALLOWED_LANGUAGES:
        raise ValueError(f"Unsupported language: {language}")

    user = await upsert_user(session, telegram_user)
    user.language = normalized
    await session.flush()
    return user


def normalize_movement_threshold(value: float) -> float:
    normalized = round(float(value), 2)
    if normalized not in ALLOWED_MOVEMENT_THRESHOLDS:
        raise ValueError(f"Unsupported movement threshold: {value}")
    return normalized


async def set_movement_threshold(
    session: AsyncSession,
    telegram_user: Any,
    threshold: float,
) -> User:
    user = await upsert_user(session, telegram_user)
    user.movement_threshold = normalize_movement_threshold(threshold)
    await session.flush()
    return user


def normalize_min_alert_volume(value: float) -> float:
    normalized = float(value)
    if normalized not in ALLOWED_MIN_ALERT_VOLUMES:
        raise ValueError(f"Unsupported alert volume: {value}")
    return normalized


async def set_min_volume_for_alerts(
    session: AsyncSession,
    telegram_user: Any,
    volume: float,
) -> User:
    user = await upsert_user(session, telegram_user)
    user.min_volume_for_alerts = normalize_min_alert_volume(volume)
    await session.flush()
    return user


async def get_notification_users(session: AsyncSession) -> list[User]:
    result = await session.execute(
        select(User).where(User.notifications_enabled.is_(True))
    )
    return list(result.scalars().all())


async def get_daily_digest_users(session: AsyncSession) -> list[User]:
    result = await session.execute(
        select(User).where(User.daily_digest_enabled.is_(True))
    )
    return list(result.scalars().all())


async def add_market_to_watchlist(
    session: AsyncSession,
    telegram_user: Any,
    market: Market,
) -> tuple[UserWatchlist, bool]:
    user = await upsert_user(session, telegram_user)
    result = await session.execute(
        select(UserWatchlist).where(
            UserWatchlist.user_id == user.id,
            UserWatchlist.market_id == market.id,
        )
    )
    existing = result.scalar_one_or_none()
    if existing is not None:
        return existing, False

    item = UserWatchlist(
        user_id=user.id,
        telegram_user_id=user.telegram_id,
        market_id=market.id,
        market_title=market.question,
        market_url=market.url,
        initial_probability=market.yes_probability,
        last_probability=market.yes_probability,
    )
    session.add(item)
    await session.flush()
    return item, True


async def update_watchlist_probability(
    session: AsyncSession,
    item: UserWatchlist,
    market: Market,
) -> UserWatchlist:
    item.market_title = market.question
    item.market_url = market.url
    item.last_probability = market.yes_probability
    await session.flush()
    return item


async def get_user_watchlist(
    session: AsyncSession,
    telegram_user: Any,
) -> list[UserWatchlist]:
    user = await upsert_user(session, telegram_user)
    result = await session.execute(
        select(UserWatchlist)
        .where(UserWatchlist.user_id == user.id)
        .order_by(desc(UserWatchlist.created_at), desc(UserWatchlist.id))
    )
    return list(result.scalars().all())


async def remove_watchlist_item(
    session: AsyncSession,
    telegram_user: Any,
    item_id: int,
) -> bool:
    user = await upsert_user(session, telegram_user)
    result = await session.execute(
        select(UserWatchlist).where(
            UserWatchlist.id == item_id,
            UserWatchlist.user_id == user.id,
        )
    )
    item = result.scalar_one_or_none()
    if item is None:
        return False

    await session.delete(item)
    await session.flush()
    return True


def normalize_topic(topic: str) -> str:
    return " ".join(topic.lower().strip().split())[:80]


async def add_user_topic(
    session: AsyncSession,
    telegram_user: Any,
    topic: str,
) -> tuple[UserTopic, bool]:
    user = await upsert_user(session, telegram_user)
    normalized = normalize_topic(topic)
    if not normalized:
        raise ValueError("Topic is required")

    result = await session.execute(
        select(UserTopic).where(
            UserTopic.telegram_user_id == user.telegram_id,
            UserTopic.topic == normalized,
        )
    )
    existing = result.scalar_one_or_none()
    if existing is not None:
        return existing, False

    item = UserTopic(telegram_user_id=user.telegram_id, topic=normalized)
    session.add(item)
    await session.flush()
    return item, True


async def get_user_topics(
    session: AsyncSession,
    telegram_user_or_id: Any,
) -> list[UserTopic]:
    telegram_id = (
        telegram_user_or_id
        if isinstance(telegram_user_or_id, int)
        else getattr(telegram_user_or_id, "id", None)
    )
    if telegram_id is None:
        raise ValueError("Telegram user id is required")

    result = await session.execute(
        select(UserTopic)
        .where(UserTopic.telegram_user_id == telegram_id)
        .order_by(desc(UserTopic.created_at), desc(UserTopic.id))
    )
    return list(result.scalars().all())


async def remove_user_topic(
    session: AsyncSession,
    telegram_user: Any,
    topic_id: int,
) -> bool:
    user = await upsert_user(session, telegram_user)
    result = await session.execute(
        select(UserTopic).where(
            UserTopic.id == topic_id,
            UserTopic.telegram_user_id == user.telegram_id,
        )
    )
    item = result.scalar_one_or_none()
    if item is None:
        return False
    await session.delete(item)
    await session.flush()
    return True


async def save_market_snapshots(
    session: AsyncSession,
    markets: Sequence[Market],
) -> None:
    for market in markets:
        session.add(
            MarketSnapshot(
                market_id=market.id,
                slug=market.slug,
                question=market.question,
                yes_probability=market.yes_probability,
                volume=market.volume,
                end_date=market.end_date,
                market_url=market.url,
                raw_data=dict(market.raw),
            )
        )
    await session.flush()


async def get_latest_snapshots(
    session: AsyncSession,
    market_ids: Iterable[str],
) -> dict[str, MarketSnapshot]:
    snapshots: dict[str, MarketSnapshot] = {}
    for market_id in set(market_ids):
        result = await session.execute(
            select(MarketSnapshot)
            .where(MarketSnapshot.market_id == market_id)
            .order_by(desc(MarketSnapshot.created_at), desc(MarketSnapshot.id))
            .limit(1)
        )
        snapshot = result.scalar_one_or_none()
        if snapshot is not None:
            snapshots[market_id] = snapshot
    return snapshots


async def get_recent_snapshots(
    session: AsyncSession,
    market_id: str,
    limit: int = 8,
) -> list[MarketSnapshot]:
    result = await session.execute(
        select(MarketSnapshot)
        .where(MarketSnapshot.market_id == market_id)
        .order_by(desc(MarketSnapshot.created_at), desc(MarketSnapshot.id))
        .limit(limit)
    )
    return list(reversed(result.scalars().all()))


async def alert_sent_recently(
    session: AsyncSession,
    telegram_user_id: int,
    market_id: str,
    alert_type: str,
    cooldown_hours: int = 6,
) -> bool:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=cooldown_hours)
    result = await session.execute(
        select(func.count(UserAlertLog.id)).where(
            UserAlertLog.telegram_user_id == telegram_user_id,
            UserAlertLog.market_id == market_id,
            UserAlertLog.alert_type == alert_type,
            UserAlertLog.sent_at >= cutoff,
        )
    )
    return (result.scalar_one() or 0) > 0


async def log_alert_sent(
    session: AsyncSession,
    telegram_user_id: int,
    market_id: str,
    alert_type: str,
) -> UserAlertLog:
    item = UserAlertLog(
        telegram_user_id=telegram_user_id,
        market_id=market_id,
        alert_type=alert_type,
    )
    session.add(item)
    await session.flush()
    return item
