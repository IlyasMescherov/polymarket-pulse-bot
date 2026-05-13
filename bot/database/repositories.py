from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import MarketSnapshot, User
from bot.services.polymarket_client import Market


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


async def get_notification_users(session: AsyncSession) -> list[User]:
    result = await session.execute(
        select(User).where(User.notifications_enabled.is_(True))
    )
    return list(result.scalars().all())


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

