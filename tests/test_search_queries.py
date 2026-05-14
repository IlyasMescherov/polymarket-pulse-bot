from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from bot.database.models import Base
from bot.database.repositories import create_search_query, get_top_search_queries


@pytest.mark.asyncio
async def test_search_query_tracking_normalizes_and_ranks_queries() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        first = await create_search_query(session, 10, " Bitcoin ", 4)
        await create_search_query(session, 11, "bitcoin", 2)
        await create_search_query(session, 10, "Fed", -1)
        await session.commit()

    async with session_factory() as session:
        top_queries = await get_top_search_queries(session, limit=2)

    assert first.query == "bitcoin"
    assert first.results_count == 4
    assert top_queries == [("bitcoin", 2), ("fed", 1)]

    await engine.dispose()
