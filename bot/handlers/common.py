from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.database.models import User
from bot.database.repositories import upsert_user
from bot.utils.i18n import DEFAULT_LANGUAGE


async def load_user(
    session_factory: async_sessionmaker[AsyncSession],
    telegram_user: Any | None,
) -> User | None:
    if telegram_user is None:
        return None

    async with session_factory() as session:
        try:
            user = await upsert_user(session, telegram_user)
            await session.commit()
            return user
        except Exception:
            await session.rollback()
            raise


def user_language(user: User | None) -> str:
    return user.language if user is not None else DEFAULT_LANGUAGE
