from __future__ import annotations

from types import SimpleNamespace

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from bot.database.models import Base
from bot.database.repositories import content_hash_exists
from bot.services.content_publisher import content_hash
from bot.services.x_publisher import XPublisher


class FakeBot:
    def __init__(self) -> None:
        self.sent: list[tuple[int, str]] = []

    async def send_message(
        self,
        chat_id: int,
        text: str,
        disable_web_page_preview: bool = True,
    ) -> None:
        self.sent.append((chat_id, text))


def _settings(**overrides: object) -> SimpleNamespace:
    values = {
        "admin_telegram_ids": frozenset({100}),
        "x_drafts_enabled": True,
        "x_posting_mode": "draft",
        "auto_x_posting_enabled": False,
        "x_api_key": None,
        "x_api_secret": None,
        "x_access_token": None,
        "x_access_token_secret": None,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


async def _session_factory() -> async_sessionmaker:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest.mark.asyncio
async def test_x_publisher_creates_draft_without_auto_publishing() -> None:
    fake_bot = FakeBot()
    session_factory = await _session_factory()
    publisher = XPublisher(fake_bot, session_factory, _settings())

    result = await publisher.create_x_draft("draft text", post_type="today_pulse")

    assert result.status == "draft"
    assert result.draft_created is True
    assert fake_bot.sent[0][0] == 100
    assert "Copy and publish manually." in fake_bot.sent[0][1]
    async with session_factory() as session:
        assert await content_hash_exists(session, "x_draft", content_hash("draft text"))


@pytest.mark.asyncio
async def test_x_publisher_skips_duplicate_draft() -> None:
    fake_bot = FakeBot()
    publisher = XPublisher(fake_bot, await _session_factory(), _settings())

    first = await publisher.create_x_draft("draft text")
    second = await publisher.create_x_draft("draft text")

    assert first.status == "draft"
    assert second.status == "skipped"
    assert len(fake_bot.sent) == 1
