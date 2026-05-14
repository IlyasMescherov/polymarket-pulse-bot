from __future__ import annotations

from dataclasses import dataclass

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from bot.database.models import Base
from bot.database.repositories import (
    add_market_to_watchlist,
    get_user_watchlist,
    remove_watchlist_item,
    set_movement_threshold,
)
from bot.services.polymarket_client import Market


@dataclass(slots=True)
class TelegramUser:
    id: int
    username: str = "tester"
    first_name: str = "Test"
    last_name: str = "User"


def _market() -> Market:
    return Market(
        id="123",
        question="Will this repository test pass?",
        slug="will-this-repository-test-pass",
        yes_probability=0.7,
        volume=1000,
        end_date=None,
        url="https://polymarket.com/market/will-this-repository-test-pass",
        raw={},
    )


@pytest.mark.asyncio
async def test_watchlist_repository_adds_deduplicates_and_removes() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    telegram_user = TelegramUser(id=42)

    async with session_factory() as session:
        item, created = await add_market_to_watchlist(
            session,
            telegram_user,
            _market(),
        )
        duplicate, duplicate_created = await add_market_to_watchlist(
            session,
            telegram_user,
            _market(),
        )
        await session.commit()

    assert created is True
    assert duplicate_created is False
    assert duplicate.id == item.id

    async with session_factory() as session:
        items = await get_user_watchlist(session, telegram_user)
        removed = await remove_watchlist_item(session, telegram_user, items[0].id)
        await session.commit()

    assert len(items) == 1
    assert removed is True

    async with session_factory() as session:
        assert await get_user_watchlist(session, telegram_user) == []

    await engine.dispose()


@pytest.mark.asyncio
async def test_threshold_setting_updates_user() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    telegram_user = TelegramUser(id=43)

    async with session_factory() as session:
        user = await set_movement_threshold(session, telegram_user, 0.15)
        await session.commit()

    assert user.movement_threshold == 0.15

    async with session_factory() as session:
        with pytest.raises(ValueError):
            await set_movement_threshold(session, telegram_user, 0.12)

    await engine.dispose()
