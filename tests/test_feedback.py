from __future__ import annotations

from dataclasses import dataclass

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from bot.database.models import Base
from bot.database.repositories import create_user_feedback, get_recent_feedback
from bot.handlers.admin import format_admin_feedback


@dataclass(slots=True)
class TelegramUser:
    id: int
    username: str | None = "tester"


@pytest.mark.asyncio
async def test_feedback_repository_saves_recent_messages() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        await create_user_feedback(session, TelegramUser(id=10), "Please add group mode")
        await create_user_feedback(session, TelegramUser(id=11, username=None), "Nice bot")
        await session.commit()

    async with session_factory() as session:
        feedback = await get_recent_feedback(session, limit=10)

    assert len(feedback) == 2
    assert feedback[0].message == "Nice bot"
    assert feedback[1].username == "tester"

    await engine.dispose()


def test_admin_feedback_formatter_handles_empty_and_messages() -> None:
    assert "No feedback yet" in format_admin_feedback([])

    class Item:
        telegram_user_id = 42
        username = "pulse"
        message = "Looks useful"

    text = format_admin_feedback([Item()])

    assert "@pulse: Looks useful" in text
