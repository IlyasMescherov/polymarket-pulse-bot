from __future__ import annotations

from datetime import datetime, timezone

from bot.services.news_impact_engine import (
    classify_news_impact,
    classify_news_impact_from_matches,
)
from bot.services.event_matching_engine import MarketEventMatch
from bot.services.source_adapters.base import ExternalNewsItem


def _event(
    *,
    title: str = "White House comments on Iran diplomacy",
    source_type: str = "official",
    source_name: str = "White House",
    urgency_score: float = 80,
    credibility_score: float = 94,
    url: str = "https://example.com/official",
) -> ExternalNewsItem:
    return ExternalNewsItem(
        source_type=source_type,
        source_name=source_name,
        source_url="https://example.com/feed",
        title=title,
        summary="Iran diplomacy and US policy are part of the latest update.",
        url=url,
        published_at=datetime(2026, 5, 16, tzinfo=timezone.utc),
        category="politics",
        entities=("iran", "trump"),
        topics=("diplomacy",),
        urgency_score=urgency_score,
        credibility_score=credibility_score,
    )


def _market() -> dict:
    return {
        "title": 'Will Trump say "Iran" during public remarks?',
        "category": "politics",
        "pulse_score": 72,
        "movement": 4,
        "volume": 200_000,
    }


def test_official_news_impact_is_high_confidence() -> None:
    impact = classify_news_impact(_market(), events=[_event()], language="en")

    assert impact.impact_type == "official_confirmed"
    assert impact.impact_label == "Official source confirmed"
    assert impact.confidence_level == "high"
    assert impact.official_source_signal is True


def test_multiple_sources_classified_without_official_source() -> None:
    first = _event(source_type="rss", source_name="Reuters", credibility_score=82, url="https://example.com/1")
    second = _event(source_type="rss", source_name="BBC", credibility_score=80, url="https://example.com/2")

    impact = classify_news_impact(_market(), events=[first, second], language="en")

    assert impact.impact_type == "multiple_sources"
    assert impact.source_count == 2
    assert impact.confidence_level in {"medium", "high"}


def test_social_only_context_lowers_confidence() -> None:
    impact = classify_news_impact(
        _market(),
        events=[_event(source_type="x", source_name="Public X", credibility_score=45)],
        language="en",
    )

    assert impact.impact_type == "social_only"
    assert impact.confidence_level == "low"


def test_market_moved_without_news_classified_correctly() -> None:
    impact = classify_news_impact(
        {"title": "Will Bitcoin hit a new high?", "pulse_score": 82, "movement": 8, "volume": 500_000},
        events=[],
        language="en",
    )

    assert impact.impact_type == "market_moved_without_news"
    assert impact.impact_label == "Market moved without strong news"


def test_news_without_market_reaction_classified_from_matches() -> None:
    event = _event(source_type="rss", source_name="AP", credibility_score=82)
    impact = classify_news_impact_from_matches(
        [MarketEventMatch(event=event, relevance_score=60, match_reason="matched entities: iran")],
        reaction_score=10,
        language="en",
    )

    assert impact.impact_type == "news_without_market_reaction"


def test_news_impact_has_no_advice_language() -> None:
    impact = classify_news_impact(_market(), events=[_event()], language="en")
    text = " ".join(str(value).lower() for value in impact.as_dict().values())

    for phrase in ("buy", "sell", "bet", "good bet", "guaranteed", "покупай", "продавай", "ставь"):
        assert phrase not in text
