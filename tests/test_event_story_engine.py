from __future__ import annotations

from datetime import datetime, timezone

from bot.services.event_story_engine import (
    build_event_stories,
    enrich_markets_with_stories,
    select_top_story,
)
from bot.services.source_adapters.base import ExternalNewsItem


def _market(
    market_id: str,
    title: str,
    *,
    event_slug: str | None = None,
    event_title: str | None = None,
    category: str = "politics",
    pulse_score: int = 65,
    volume: float = 100_000,
) -> dict:
    raw = {}
    if event_slug:
        raw["eventSlug"] = event_slug
    if event_title:
        raw["eventTitle"] = event_title
    return {
        "market_id": market_id,
        "id": market_id,
        "title": title,
        "question": title,
        "category": category,
        "pulse_score": pulse_score,
        "volume": volume,
        "movement": 2,
        "raw": raw,
    }


def _api_object(market: dict) -> dict:
    return {
        "market_id": market["market_id"],
        "title": market["title"],
        "category": market["category"],
        "pulse_score": market["pulse_score"],
        "volume": market["volume"],
        "movement": market["movement"],
        "dominant_outcome_label": "NO",
        "runner_up_label": "YES",
        "news_urgency": "medium",
    }


def _event(
    *,
    source_type: str = "official",
    source_name: str = "White House",
    url: str = "https://example.com/iran",
    urgency_score: float = 82,
) -> ExternalNewsItem:
    return ExternalNewsItem(
        source_type=source_type,
        source_name=source_name,
        source_url="https://example.com/feed",
        title="Iran diplomacy update from US officials",
        summary="Trump, Iran, and diplomacy are in the latest public update.",
        url=url,
        published_at=datetime(2026, 5, 16, tzinfo=timezone.utc),
        category="politics",
        entities=("iran", "trump"),
        topics=("diplomacy",),
        urgency_score=urgency_score,
        credibility_score=94 if source_type == "official" else 80,
    )


def test_markets_with_same_event_slug_grouped_together() -> None:
    markets = [
        _market("1", "Will Trump mention Iran?", event_slug="iran-us", event_title="Iran / US diplomacy"),
        _market("2", "Will Iran meet US diplomats?", event_slug="iran-us", event_title="Iran / US diplomacy"),
    ]

    stories = build_event_stories(markets, market_api_objects=[_api_object(item) for item in markets], events=[])

    assert len(stories) == 1
    assert stories[0].story_title == "Iran / US diplomacy"
    assert stories[0].related_market_ids == ("1", "2")


def test_markets_with_shared_entities_grouped_together() -> None:
    markets = [
        _market("1", "Will Trump mention Iran?"),
        _market("2", "Will Iran reach a diplomacy deal?"),
    ]

    stories = build_event_stories(markets, market_api_objects=[_api_object(item) for item in markets], events=[])

    assert len(stories) == 1
    assert stories[0].story_title in {"Iran / Trump", "Iran / US diplomacy"}


def test_unrelated_single_markets_do_not_create_artificial_stories() -> None:
    markets = [
        _market("1", "Will Bitcoin hit a new high?", category="crypto"),
        _market("2", "Will a football match go to extra time?", category="sports"),
    ]

    stories = build_event_stories(markets, market_api_objects=[_api_object(item) for item in markets], events=[])

    assert stories == []
    assert select_top_story(stories) is None


def test_single_market_with_official_source_can_be_top_story() -> None:
    market = _market("1", 'Will Trump say "Iran" during remarks?')

    stories = build_event_stories([market], market_api_objects=[_api_object(market)], events=[_event()])

    assert stories
    assert stories[0].official_source_signal is True
    assert select_top_story(stories)["story_title"]


def test_weak_story_does_not_become_top_story() -> None:
    market = _market("1", "Will a niche culture event happen?", category="culture", pulse_score=28, volume=5_000)
    weak_event = _event(source_type="rss", source_name="Small Blog", url="https://example.com/weak", urgency_score=20)

    stories = build_event_stories([market], market_api_objects=[_api_object(market)], events=[weak_event])

    assert stories == []
    assert select_top_story(stories) is None


def test_top_story_prefers_official_and_fresh_context() -> None:
    weak_pair = [
        _market("1", "Will Bitcoin move today?", category="crypto", event_slug="btc", event_title="Bitcoin volatility"),
        _market("2", "Will Bitcoin hit a price level?", category="crypto", event_slug="btc", event_title="Bitcoin volatility"),
    ]
    official_market = _market("3", 'Will Trump say "Iran" during remarks?', pulse_score=80)
    markets = [*weak_pair, official_market]

    stories = build_event_stories(
        markets,
        market_api_objects=[_api_object(item) for item in markets],
        events=[_event()],
    )

    top = select_top_story(stories)
    assert top is not None
    assert top["news_impact_type"] == "official_confirmed"


def test_enrich_markets_only_adds_story_fields_for_qualified_story() -> None:
    grouped = [
        _market("1", "Will Trump mention Iran?", event_slug="iran-us", event_title="Iran / US diplomacy"),
        _market("2", "Will Iran meet US diplomats?", event_slug="iran-us", event_title="Iran / US diplomacy"),
    ]
    weak = _market("3", "Will a niche culture event happen?", category="culture", pulse_score=20, volume=1_000)
    markets = [*grouped, weak]
    api_objects = [_api_object(item) for item in markets]
    stories = build_event_stories(markets, market_api_objects=api_objects, events=[])
    enriched = enrich_markets_with_stories(api_objects, stories)

    assert enriched[0]["story_title"] == "Iran / US diplomacy"
    assert enriched[1]["related_markets_count"] == 2
    assert "story_title" not in enriched[2]


def test_story_output_has_no_advice_language() -> None:
    markets = [
        _market("1", "Will Trump mention Iran?", event_slug="iran-us", event_title="Iran / US diplomacy"),
        _market("2", "Will Iran meet US diplomats?", event_slug="iran-us", event_title="Iran / US diplomacy"),
    ]
    stories = build_event_stories(markets, market_api_objects=[_api_object(item) for item in markets], events=[])
    text = " ".join(str(story.as_dict()).lower() for story in stories)

    for phrase in ("buy", "sell", "bet", "good bet", "guaranteed", "покупай", "продавай", "ставь"):
        assert phrase not in text
