from __future__ import annotations

from types import SimpleNamespace

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from bot.database.models import Base
from bot.database.repositories import content_hash_exists
from bot.services.channel_publisher import ChannelPublisher
from bot.services.content_publisher import content_hash


class FakeBot:
    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []

    async def send_message(
        self,
        chat_id: str,
        text: str,
        disable_web_page_preview: bool = True,
    ) -> None:
        self.sent.append((chat_id, text))


def _settings(**overrides: object) -> SimpleNamespace:
    values = {
        "project_channel_id": "@PulseMarketAI",
        "auto_channel_posting_enabled": False,
        "auto_channel_posting_min_hours_between_posts": 20,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


async def _session_factory() -> async_sessionmaker:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest.mark.asyncio
async def test_channel_publisher_does_not_post_when_disabled() -> None:
    fake_bot = FakeBot()
    publisher = ChannelPublisher(fake_bot, await _session_factory(), _settings())

    result = await publisher.publish_to_telegram_channel("hello")

    assert result.status == "skipped"
    assert fake_bot.sent == []


@pytest.mark.asyncio
async def test_channel_publisher_posts_when_manual_bypass_enabled() -> None:
    fake_bot = FakeBot()
    session_factory = await _session_factory()
    publisher = ChannelPublisher(fake_bot, session_factory, _settings())

    result = await publisher.publish_to_telegram_channel(
        "hello",
        bypass_enabled=True,
    )

    assert result.status == "published"
    assert fake_bot.sent == [("@PulseMarketAI", "hello")]
    async with session_factory() as session:
        assert await content_hash_exists(session, "telegram_channel", content_hash("hello"))


@pytest.mark.asyncio
async def test_channel_publisher_skips_duplicate_content() -> None:
    fake_bot = FakeBot()
    publisher = ChannelPublisher(fake_bot, await _session_factory(), _settings())

    first = await publisher.publish_to_telegram_channel("hello", bypass_enabled=True)
    second = await publisher.publish_to_telegram_channel("hello", bypass_enabled=True)

    assert first.status == "published"
    assert second.status == "skipped"
    assert len(fake_bot.sent) == 1


@pytest.mark.asyncio
async def test_channel_publisher_respects_cooldown() -> None:
    fake_bot = FakeBot()
    publisher = ChannelPublisher(fake_bot, await _session_factory(), _settings())

    first = await publisher.publish_to_telegram_channel("hello 1", bypass_enabled=True)
    second = await publisher.publish_to_telegram_channel("hello 2", bypass_enabled=True)

    assert first.status == "published"
    assert second.status == "skipped"
    assert "Cooldown" in second.message
    assert len(fake_bot.sent) == 1
