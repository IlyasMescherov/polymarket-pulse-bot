from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest
from aiohttp.test_utils import make_mocked_request

from bot.services.health_server import HealthServer
from bot.services.polymarket_client import Market
from bot.services.smart_money_analyzer import MarketActivity, TraderScore


def _market(market_id: str = "1") -> Market:
    return Market(
        id=market_id,
        question="Will Bitcoin hit $150k by December 31, 2026?",
        slug="will-bitcoin-hit-150k-by-december-31-2026",
        yes_probability=0.63,
        volume=120_000,
        end_date=datetime(2026, 12, 31, tzinfo=timezone.utc),
        url="https://polymarket.com/market/will-bitcoin-hit-150k-by-december-31-2026",
        raw={},
    )


def _custom_market(market_id: str, question: str, raw: dict | None = None) -> Market:
    return Market(
        id=market_id,
        question=question,
        slug=question.lower().replace(" ", "-").replace("?", "")[:60],
        yes_probability=0.42,
        volume=40_000,
        end_date=datetime(2026, 12, 31, tzinfo=timezone.utc),
        url="https://polymarket.com/market/example",
        raw=raw or {},
    )


class FakeMarketAnalyzer:
    async def get_hot_markets(self, limit: int = 5) -> list[Market]:
        return [_market("hot")]

    async def get_new_markets(self, limit: int = 5) -> list[Market]:
        return [_market("new")]

    async def search_markets(self, query: str, limit: int = 5) -> list[Market]:
        return [_market("search")]


class FakeNoStoryMarketAnalyzer:
    async def get_hot_markets(self, limit: int = 5) -> list[Market]:
        return [_custom_market("hot", "Will a local music award happen?", {"category": "Culture"})]

    async def get_new_markets(self, limit: int = 5) -> list[Market]:
        return [_custom_market("new", "Will a football match go to extra time?", {"category": "Sports"})]


class FakeSmartMoneyAnalyzer:
    async def active_markets(self, limit: int = 5) -> list[MarketActivity]:
        return [
            MarketActivity(
                market_id="market-1",
                market_title="Will Bitcoin hit $150k by December 31, 2026?",
                amount_usd=42_000,
                trades_count=3,
                participant_count=2,
            )
        ]

    async def public_traders(self, limit: int = 5) -> list[TraderScore]:
        return [
            TraderScore(
                wallet_address="0x1111111111111111111111111111111111111111",
                display_name=None,
                score=74,
                label="High public activity",
                volume=500_000,
                trades_count=42,
                rank=1,
            )
        ]


def _payload(response) -> dict:
    return json.loads(response.text)


@pytest.mark.asyncio
async def test_miniapp_hot_api_shape() -> None:
    server = HealthServer(
        "127.0.0.1",
        0,
        engine=object(),
        market_analyzer=FakeMarketAnalyzer(),
    )

    response = await server._api_hot_markets(make_mocked_request("GET", "/api/markets/hot"))
    payload = _payload(response)

    assert payload["message"] == "ok"
    assert payload["data"][0]["market_id"] == "hot"
    assert payload["data"][0]["probability"] == 63
    assert payload["data"][0]["probability_label"] == "63%"
    assert payload["data"][0]["probability_interpretation"] == "Likely"
    assert payload["data"][0]["pulse_score"] >= 0
    assert payload["data"][0]["pulse_description"] == "How interesting this market looks today."
    assert payload["data"][0]["market_health_score"] >= 0
    assert payload["data"][0]["market_mood_label"]
    assert payload["data"][0]["market_mood_reason"]
    assert payload["data"][0]["category"]
    assert payload["data"][0]["category_label"]
    assert payload["data"][0]["why_people_care"]
    assert payload["data"][0]["simple_read"]
    assert payload["data"][0]["what_to_watch"]
    assert payload["data"][0]["attention_summary"]
    assert payload["data"][0]["topic_narrative"]
    assert payload["data"][0]["quick_take"]
    assert payload["data"][0]["what_happened"]
    assert payload["data"][0]["main_tension"]
    assert payload["data"][0]["what_this_means"]
    assert payload["data"][0]["attention_vs_conviction"]
    assert payload["data"][0]["insight_strength"]
    assert payload["data"][0]["confidence_level"]
    assert payload["data"][0]["market_memory_summary"]
    assert payload["data"][0]["market_regime"]
    assert payload["data"][0]["market_regime_key"]
    assert payload["data"][0]["market_heat"]
    assert payload["data"][0]["market_heat_key"]
    assert payload["data"][0]["confirmation_level"]
    assert payload["data"][0]["confirmation_level_key"]
    assert payload["data"][0]["error_risk"]
    assert payload["data"][0]["error_risk_key"]
    assert payload["data"][0]["time_pressure"]
    assert payload["data"][0]["time_pressure_key"]
    assert payload["data"][0]["market_depth"]
    assert payload["data"][0]["market_depth_key"]
    assert payload["data"][0]["ai_verdict"]
    assert payload["data"][0]["ai_verdict_key"]
    assert payload["data"][0]["indicator_summary"]
    assert payload["data"][0]["side_summary"]
    assert payload["data"][0]["dominant_side"]
    assert "yes_probability" in payload["data"][0]
    assert "no_probability" in payload["data"][0]
    assert "yes_price" in payload["data"][0]
    assert "no_price" in payload["data"][0]
    assert payload["data"][0]["side_balance"]
    assert payload["data"][0]["side_tension"]
    assert payload["data"][0]["side_confidence"]
    assert payload["data"][0]["opposite_interest"]
    assert payload["data"][0]["side_verdict"]
    assert payload["data"][0]["side_risk_note"]
    assert payload["data"][0]["outcome_type"]
    assert isinstance(payload["data"][0]["display_outcomes"], list)
    assert payload["data"][0]["dominant_outcome_label"]
    assert "dominant_outcome_probability" in payload["data"][0]
    assert "runner_up_label" in payload["data"][0]
    assert "runner_up_probability" in payload["data"][0]
    assert "outcome_spread" in payload["data"][0]
    assert payload["data"][0]["outcome_balance_summary"]
    assert payload["data"][0]["should_use_yes_no"] is True
    assert payload["data"][0]["regime_reason"]
    assert payload["data"][0]["memory_pattern"]
    assert payload["data"][0]["changed_since_last_seen"]
    assert payload["data"][0]["historical_context"]
    assert payload["data"][0]["resolution_note"]
    assert payload["data"][0]["category_voice"]
    assert isinstance(payload["data"][0]["related_topics"], list)
    assert payload["data"][0]["news_context"]
    assert "latest_relevant_news" in payload["data"][0]
    assert "source_count" in payload["data"][0]
    assert "credible_source_count" in payload["data"][0]
    assert "social_heat" in payload["data"][0]
    assert "telegram_heat" in payload["data"][0]
    assert "x_heat" in payload["data"][0]
    assert "official_source_signal" in payload["data"][0]
    assert "news_urgency" in payload["data"][0]
    assert payload["data"][0]["why_moving_now"]
    assert payload["data"][0]["what_changed_outside_market"]
    assert payload["data"][0]["confidence_from_news"]
    assert payload["data"][0]["news_risk_note"]
    assert payload["data"][0]["url"].startswith("https://polymarket.com")


@pytest.mark.asyncio
async def test_miniapp_today_api_shape() -> None:
    server = HealthServer(
        "127.0.0.1",
        0,
        engine=object(),
        market_analyzer=FakeMarketAnalyzer(),
    )

    response = await server._api_today(make_mocked_request("GET", "/api/today"))
    payload = _payload(response)

    assert payload["message"] == "ok"
    assert payload["data"]
    assert "why_it_matters" in payload["data"][0]
    assert "why_people_care" in payload["data"][0]
    assert "risk_flags" in payload["data"][0]
    assert "market_heat" in payload["data"][0]
    assert "confirmation_level" in payload["data"][0]
    assert "error_risk" in payload["data"][0]
    assert "time_pressure" in payload["data"][0]
    assert "market_depth" in payload["data"][0]
    assert "ai_verdict" in payload["data"][0]
    assert "indicator_summary" in payload["data"][0]
    assert "dominant_side" in payload["data"][0]
    assert "side_verdict" in payload["data"][0]
    assert payload["narrative"]
    assert payload["interpretation"]
    assert payload["what_changed"]
    assert payload["changed_since_last_brief"]
    assert isinstance(payload["category_summaries"], dict)
    assert isinstance(payload["news_themes"], list)
    assert isinstance(payload["story_clusters"], list)
    assert payload["top_story"]
    assert "story_title" in payload["top_story"]
    assert payload["top_story"]["what_happened"]
    assert payload["top_story"]["likely_catalyst"]
    assert payload["top_story"]["catalyst_evidence"]
    assert payload["top_story"]["price_probability_context"]
    assert payload["top_story"]["what_to_verify_next"]
    assert "market_story_id" in payload["data"][0]
    assert payload["data"][0]["story_what_happened"]
    assert payload["data"][0]["likely_catalyst"]
    assert payload["data"][0]["catalyst_evidence"]
    assert "news_impact_type" in payload["data"][0]
    assert "news_context" in payload["data"][0]


@pytest.mark.asyncio
async def test_today_api_falls_back_when_story_clusters_are_weak() -> None:
    server = HealthServer(
        "127.0.0.1",
        0,
        engine=object(),
        market_analyzer=FakeNoStoryMarketAnalyzer(),
    )

    response = await server._api_today(make_mocked_request("GET", "/api/today"))
    payload = _payload(response)

    assert payload["message"] == "ok"
    assert payload["data"]
    assert payload["story_clusters"] == []
    assert payload["top_story"] is None
    assert "story_title" not in payload["data"][0]
    assert payload["data"][0]["title"]


@pytest.mark.asyncio
async def test_miniapp_smart_money_api_shape() -> None:
    server = HealthServer(
        "127.0.0.1",
        0,
        engine=object(),
        smart_money_analyzer=FakeSmartMoneyAnalyzer(),
    )

    active_response = await server._api_smart_money_active(
        make_mocked_request("GET", "/api/smart-money/active")
    )
    traders_response = await server._api_smart_money_traders(
        make_mocked_request("GET", "/api/smart-money/traders")
    )

    active_payload = _payload(active_response)
    traders_payload = _payload(traders_response)

    assert active_payload["data"][0]["public_activity"] == 42000
    assert active_payload["data"][0]["trades_count"] == 3
    assert active_payload["data"][0]["why_it_matters"]
    assert active_payload["data"][0]["quick_take"]
    assert active_payload["data"][0]["main_tension"]
    assert active_payload["data"][0]["what_this_means"]
    assert active_payload["data"][0]["attention_vs_conviction"]
    assert active_payload["data"][0]["insight_strength"]
    assert active_payload["data"][0]["market_memory_summary"]
    assert active_payload["data"][0]["market_regime"]
    assert active_payload["data"][0]["market_heat"]
    assert active_payload["data"][0]["confirmation_level"]
    assert active_payload["data"][0]["error_risk"]
    assert active_payload["data"][0]["time_pressure"]
    assert active_payload["data"][0]["market_depth"]
    assert active_payload["data"][0]["ai_verdict"]
    assert active_payload["data"][0]["dominant_side"]
    assert active_payload["data"][0]["side_verdict"]
    assert active_payload["data"][0]["news_context"]
    assert traders_payload["data"][0]["wallet"] == "0x1111...1111"
    assert traders_payload["data"][0]["why_it_matters"]
    assert traders_payload["data"][0]["trader_score"] == 74


@pytest.mark.asyncio
async def test_miniapp_search_empty_query_returns_empty_array() -> None:
    server = HealthServer(
        "127.0.0.1",
        0,
        engine=object(),
        market_analyzer=FakeMarketAnalyzer(),
    )

    response = await server._api_search(make_mocked_request("GET", "/api/search"))
    payload = _payload(response)

    assert payload["data"] == []
    assert payload["message"] == "search query is empty"


@pytest.mark.asyncio
async def test_miniapp_search_returns_ai_assisted_summary() -> None:
    server = HealthServer(
        "127.0.0.1",
        0,
        engine=object(),
        market_analyzer=FakeMarketAnalyzer(),
    )

    response = await server._api_search(make_mocked_request("GET", "/api/search?q=bitcoin"))
    payload = _payload(response)

    assert payload["message"] == "ok"
    assert payload["summary"]
    assert payload["data"][0]["simple_read"]
