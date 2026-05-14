from __future__ import annotations

from bot.services.market_analyzer import (
    filter_markets_by_category,
    filter_markets_by_query,
)
from bot.services.polymarket_client import Market


def _market(market_id: str, question: str, category: str | None = None) -> Market:
    return Market(
        id=market_id,
        question=question,
        slug=None,
        yes_probability=0.5,
        volume=100,
        end_date=None,
        url="https://polymarket.com",
        raw={"category": category} if category else {},
    )


def test_filter_markets_by_query_matches_question_tokens() -> None:
    markets = [
        _market("1", "Will Bitcoin hit a new high?"),
        _market("2", "Will the next election be close?"),
    ]

    assert [market.id for market in filter_markets_by_query(markets, "bitcoin")] == [
        "1"
    ]
    assert filter_markets_by_query(markets, "") == []


def test_filter_markets_by_category_matches_keywords() -> None:
    markets = [
        _market("1", "Will BTC finish above $100k?"),
        _market("2", "Will the Fed cut rates?", "Economy"),
        _market("3", "Will an NBA team win the finals?"),
    ]

    assert [market.id for market in filter_markets_by_category(markets, "crypto")] == [
        "1"
    ]
    assert [market.id for market in filter_markets_by_category(markets, "economy")] == [
        "2"
    ]
    assert [market.id for market in filter_markets_by_category(markets, "sports")] == [
        "3"
    ]
