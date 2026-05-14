from __future__ import annotations

from bot.services.market_analyzer import filter_markets_by_category
from bot.services.polymarket_client import Market


def _market(market_id: str, question: str, raw: dict[str, object]) -> Market:
    return Market(
        id=market_id,
        question=question,
        slug=None,
        yes_probability=0.5,
        volume=25_000,
        end_date=None,
        url="https://polymarket.com",
        raw=raw,
    )


def test_category_filter_uses_tags_description_and_category_fields() -> None:
    markets = [
        _market("1", "Will this bill pass?", {"tags": [{"label": "Congress"}]}),
        _market("2", "Will this model launch?", {"description": "OpenAI release"}),
        _market("3", "Will the final be close?", {"category": {"name": "NBA"}}),
        _market("4", "Will inflation fall?", {"category": "Economy"}),
    ]

    assert [market.id for market in filter_markets_by_category(markets, "politics")] == [
        "1"
    ]
    assert [market.id for market in filter_markets_by_category(markets, "ai_tech")] == [
        "2"
    ]
    assert [market.id for market in filter_markets_by_category(markets, "sports")] == [
        "3"
    ]
    assert [market.id for market in filter_markets_by_category(markets, "economy")] == [
        "4"
    ]
