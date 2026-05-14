from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from bot.database.models import Base
from bot.database.repositories import (
    count_market_link_clicks,
    count_market_link_clicks_today,
    create_market_link_click,
    get_top_clicked_markets,
)


@pytest.mark.asyncio
async def test_market_link_click_tracking_counts_and_ranks() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        await create_market_link_click(session, 10, "m1", "Bitcoin market", "hot")
        await create_market_link_click(session, 11, "m1", "Bitcoin market", "search")
        await create_market_link_click(session, 10, "m2", "Fed market", "not-real")
        await session.commit()

    async with session_factory() as session:
        top_markets = await get_top_clicked_markets(session, limit=2)
        total_clicks = await count_market_link_clicks(session)
        today_clicks = await count_market_link_clicks_today(session)

    assert total_clicks == 3
    assert today_clicks == 3
    assert top_markets[0] == ("m1", "Bitcoin market", 2)
    assert top_markets[1] == ("m2", "Fed market", 1)

    await engine.dispose()
