from __future__ import annotations

from datetime import datetime, timezone

from bot.services.event_categories import (
    category_label,
    category_options,
    classify_market_category,
    filter_markets_by_category,
)
from bot.services.polymarket_client import Market


def _market(market_id: str, question: str, raw: dict[str, object] | None = None) -> Market:
    return Market(
        id=market_id,
        question=question,
        slug=market_id,
        yes_probability=0.5,
        volume=10_000,
        end_date=datetime(2026, 12, 31, tzinfo=timezone.utc),
        url=f"https://polymarket.com/market/{market_id}",
        raw=raw or {},
    )


def test_event_categories_have_ru_and_en_labels() -> None:
    options_en = category_options("en")
    options_ru = category_options("ru")

    assert options_en[0] == {"key": "all", "label": "All"}
    assert options_ru[0] == {"key": "all", "label": "Все"}
    assert category_label("politics", "ru") == "Политика"
    assert category_label("esports", "en") == "Esports"


def test_classify_market_category_uses_title_tags_and_description() -> None:
    markets = [
        _market("p", "Will the election go to a runoff?"),
        _market("c", "Will Bitcoin hit $150k?", {"tags": ["crypto"]}),
        _market("e", "Will Team Vitality win?", {"description": "CS2 esports final"}),
        _market("g", "Will the UN pass a ceasefire resolution?", {"category": "Global"}),
    ]

    assert classify_market_category(markets[0]) == "politics"
    assert classify_market_category(markets[1]) == "crypto"
    assert classify_market_category(markets[2]) == "esports"
    assert classify_market_category(markets[3]) == "global"
    assert [market.id for market in filter_markets_by_category(markets, "crypto")] == ["c"]


def test_music_award_market_does_not_match_war_keyword() -> None:
    market = _market(
        "award",
        "Will a local music award happen this month?",
        {"category": "Culture", "description": "Local entertainment and music event"},
    )

    assert classify_market_category(market) == "culture"
