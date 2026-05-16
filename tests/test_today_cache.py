from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from aiohttp.test_utils import make_mocked_request
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from bot.database.models import Base
from bot.database.repositories import get_briefing_cache, upsert_briefing_cache
from bot.services.ai_context_engine import AIContextEngine
from bot.services.health_server import HealthServer
from bot.services.polymarket_client import Market


def _market(market_id: str, title: str | None = None) -> Market:
    return Market(
        id=market_id,
        question=title or "Will Bitcoin hit $150k by December 31, 2026?",
        slug=(title or "will-bitcoin-hit-150k").lower().replace(" ", "-")[:80],
        yes_probability=0.63,
        volume=120_000,
        end_date=datetime(2026, 12, 31, tzinfo=timezone.utc),
        url=f"https://polymarket.com/market/{market_id}",
        raw={},
    )


def _cached_payload() -> dict:
    return {
        "data": [
            {
                "market_id": "cached",
                "title": "Cached briefing market",
                "probability": 63,
                "url": "https://polymarket.com/market/cached",
            }
        ],
        "message": "ok",
        "narrative": "Cached market briefing.",
        "interpretation": "Cached response is ready.",
        "what_changed": [],
        "changed_since_last_brief": [],
        "category_summaries": {},
        "news_themes": [],
        "top_story": None,
        "story_clusters": [],
    }


def _payload(response) -> dict:
    return json.loads(response.text)


class CountingMarketAnalyzer:
    def __init__(self, *, fail: bool = False, no_story: bool = False) -> None:
        self.fail = fail
        self.no_story = no_story
        self.hot_calls = 0
        self.new_calls = 0

    async def get_hot_markets(self, limit: int = 5) -> list[Market]:
        self.hot_calls += 1
        if self.fail:
            raise RuntimeError("market fetch failed")
        if self.no_story:
            return [_market("music", "Will a local music award happen?")]
        return [_market("hot")]

    async def get_new_markets(self, limit: int = 5) -> list[Market]:
        self.new_calls += 1
        if self.fail:
            raise RuntimeError("market fetch failed")
        if self.no_story:
            return [_market("sports", "Will a football match go to extra time?")]
        return [_market("new")]


class ExplodingAIContextEngine(AIContextEngine):
    async def market_context(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        raise TimeoutError("OpenAI timeout")

    async def daily_narrative(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        raise TimeoutError("OpenAI timeout")


class InvalidJSONAIContextEngine(AIContextEngine):
    def __init__(self) -> None:
        super().__init__("test-key")

    async def _openai_chat_content(self, payload):  # type: ignore[no-untyped-def]
        return "{invalid json"


@pytest_asyncio.fixture()
async def session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        yield factory
    finally:
        await engine.dispose()


async def _store_cache(
    session_factory,
    *,
    expires_at: datetime,
    updated_at: datetime | None = None,
) -> None:
    async with session_factory() as session:
        item = await upsert_briefing_cache(
            session,
            cache_key="today:global:en",
            payload_json=_cached_payload(),
            expires_at=expires_at,
            status="ready",
        )
        if updated_at is not None:
            item.updated_at = updated_at
        await session.commit()


@pytest.mark.asyncio
async def test_fresh_cache_returns_immediately(session_factory) -> None:
    await _store_cache(session_factory, expires_at=datetime.now(timezone.utc) + timedelta(minutes=5))
    analyzer = CountingMarketAnalyzer()
    server = HealthServer(
        "127.0.0.1",
        0,
        engine=object(),
        market_analyzer=analyzer,
        session_factory=session_factory,
        enable_today_background_refresh=False,
    )

    response = await server._api_today(make_mocked_request("GET", "/api/today"))
    payload = _payload(response)

    assert payload["is_cached"] is True
    assert payload["is_stale"] is False
    assert payload["refresh_status"] == "fresh"
    assert payload["generated_at"]
    assert isinstance(payload["updated_ago_seconds"], int)
    assert payload["data"][0]["market_id"] == "cached"
    assert analyzer.hot_calls == 0
    assert analyzer.new_calls == 0


@pytest.mark.asyncio
async def test_stale_cache_returns_last_good_briefing(session_factory) -> None:
    await _store_cache(session_factory, expires_at=datetime.now(timezone.utc) - timedelta(seconds=5))
    analyzer = CountingMarketAnalyzer()
    server = HealthServer(
        "127.0.0.1",
        0,
        engine=object(),
        market_analyzer=analyzer,
        session_factory=session_factory,
        enable_today_background_refresh=False,
    )

    response = await server._api_today(make_mocked_request("GET", "/api/today"))
    payload = _payload(response)

    assert payload["is_cached"] is True
    assert payload["is_stale"] is True
    assert payload["refresh_status"] == "updating"
    assert payload["data"][0]["market_id"] == "cached"
    assert analyzer.hot_calls == 0
    assert analyzer.new_calls == 0


@pytest.mark.asyncio
async def test_missing_cache_builds_response_and_saves(session_factory) -> None:
    analyzer = CountingMarketAnalyzer()
    server = HealthServer(
        "127.0.0.1",
        0,
        engine=object(),
        market_analyzer=analyzer,
        session_factory=session_factory,
        enable_today_background_refresh=False,
    )

    response = await server._api_today(make_mocked_request("GET", "/api/today"))
    payload = _payload(response)

    assert payload["message"] == "ok"
    assert payload["data"]
    assert payload["is_cached"] is False
    assert payload["is_stale"] is False
    assert analyzer.hot_calls == 1
    assert analyzer.new_calls == 1
    async with session_factory() as session:
        assert await get_briefing_cache(session, "today:global:en") is not None


@pytest.mark.asyncio
async def test_failed_refresh_keeps_last_good(session_factory) -> None:
    old = datetime.now(timezone.utc) - timedelta(hours=2)
    await _store_cache(session_factory, expires_at=old, updated_at=old)
    server = HealthServer(
        "127.0.0.1",
        0,
        engine=object(),
        market_analyzer=CountingMarketAnalyzer(fail=True),
        session_factory=session_factory,
        enable_today_background_refresh=False,
    )

    response = await server._api_today(make_mocked_request("GET", "/api/today"))
    payload = _payload(response)

    assert payload["is_cached"] is True
    assert payload["is_stale"] is True
    assert payload["refresh_status"] == "last_good"
    assert payload["data"][0]["market_id"] == "cached"


@pytest.mark.asyncio
async def test_story_clusters_empty_still_returns_market_fallback(session_factory) -> None:
    server = HealthServer(
        "127.0.0.1",
        0,
        engine=object(),
        market_analyzer=CountingMarketAnalyzer(no_story=True),
        session_factory=session_factory,
        enable_today_background_refresh=False,
    )

    response = await server._api_today(make_mocked_request("GET", "/api/today"))
    payload = _payload(response)

    assert payload["message"] == "ok"
    assert payload["data"]
    assert payload["story_clusters"] == []
    assert payload["top_story"] is None


@pytest.mark.asyncio
async def test_openai_failure_does_not_break_today(session_factory) -> None:
    server = HealthServer(
        "127.0.0.1",
        0,
        engine=object(),
        market_analyzer=CountingMarketAnalyzer(),
        ai_context_engine=ExplodingAIContextEngine(None),
        session_factory=session_factory,
        enable_today_background_refresh=False,
    )

    response = await server._api_today(make_mocked_request("GET", "/api/today"))
    payload = _payload(response)

    assert payload["message"] == "ok"
    assert payload["data"]
    assert payload["narrative"]


@pytest.mark.asyncio
async def test_today_refresh_does_not_save_broken_ai_text_as_fresh(session_factory) -> None:
    server = HealthServer(
        "127.0.0.1",
        0,
        engine=object(),
        market_analyzer=CountingMarketAnalyzer(),
        ai_context_engine=InvalidJSONAIContextEngine(),
        session_factory=session_factory,
        enable_today_background_refresh=False,
    )

    payload = await server.refresh_today_cache(reason="test_invalid_ai")

    assert payload is not None
    assert payload["data"]
    assert payload["data"][0]["quick_take"]
    assert "{invalid json" not in json.dumps(payload)
    async with session_factory() as session:
        cached = await get_briefing_cache(session, "today:global:en")
    assert cached is not None
    assert "{invalid json" not in json.dumps(cached.payload_json)


def test_today_cache_payload_has_no_financial_advice_language() -> None:
    text = json.dumps(_cached_payload()).lower()
    for phrase in ("buy", "sell", "bet", "good bet", "guaranteed"):
        assert phrase not in text
