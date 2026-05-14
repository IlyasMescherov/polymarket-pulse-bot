from __future__ import annotations

from dataclasses import dataclass

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from bot.database.models import Base
from bot.database.repositories import (
    add_tracked_trader,
    count_large_trades_detected_today,
    count_smart_money_alerts_today,
    count_smart_money_snapshots,
    count_tracked_traders,
    create_smart_money_snapshot,
    get_recent_smart_money_snapshots,
    get_user_tracked_traders,
    log_smart_money_alert_sent,
    set_smart_money_alerts,
)


@dataclass(slots=True)
class TelegramUser:
    id: int
    username: str | None = "tester"
    first_name: str | None = "Test"
    last_name: str | None = "User"


@pytest.mark.asyncio
async def test_smart_money_repository_tracks_wallets_and_snapshots() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    user = TelegramUser(id=100)
    wallet = "0x1111111111111111111111111111111111111111"

    async with session_factory() as session:
        settings_user = await set_smart_money_alerts(session, user, True)
        item, created = await add_tracked_trader(session, user, wallet)
        duplicate, duplicate_created = await add_tracked_trader(session, user, wallet.upper())
        await create_smart_money_snapshot(
            session,
            "large_trade",
            market_id="m1",
            market_title="Bitcoin market",
            wallet_address=wallet,
            amount_usd=50_000,
        )
        await log_smart_money_alert_sent(session, user.id, "large_trade", market_id="m1")
        await session.commit()

    assert settings_user.smart_money_alerts_enabled is True
    assert created is True
    assert duplicate_created is False
    assert duplicate.id == item.id

    async with session_factory() as session:
        assert await count_tracked_traders(session) == 1
        assert await count_smart_money_snapshots(session) == 1
        assert await count_large_trades_detected_today(session) == 1
        assert await count_smart_money_alerts_today(session) == 1
        tracked = await get_user_tracked_traders(session, user)
        snapshots = await get_recent_smart_money_snapshots(session)

    assert tracked[0].wallet_address == wallet
    assert snapshots[0].market_title == "Bitcoin market"

    await engine.dispose()
