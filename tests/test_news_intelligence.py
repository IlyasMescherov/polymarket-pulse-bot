from __future__ import annotations

from datetime import datetime, timezone

from bot.services.event_matching_engine import match_events_to_market, matched_terms_from_reason
from bot.services.news_intelligence_engine import (
    NewsIntelligenceEngine,
    build_news_context,
    dedupe_events,
)
from bot.services.source_adapters.base import ExternalNewsItem, SourceConfig
from bot.services.source_adapters.rss_adapter import RSSAdapter
from bot.services.source_credibility_engine import (
    credibility_for_source,
    news_confidence,
)


def _event(
    title: str = "Trump discusses Iran with China officials",
    *,
    source_type: str = "rss",
    source_name: str = "BBC World",
    category: str = "politics",
    credibility_score: float = 78,
    url: str = "https://example.com/news/1",
) -> ExternalNewsItem:
    return ExternalNewsItem(
        source_type=source_type,
        source_name=source_name,
        source_url="https://example.com/feed.xml",
        title=title,
        summary="Iran diplomacy and US-China relations moved into focus.",
        url=url,
        published_at=datetime(2026, 5, 16, tzinfo=timezone.utc),
        category=category,
        entities=("trump", "iran", "china"),
        topics=("diplomacy",),
        urgency_score=72,
        credibility_score=credibility_score,
    )


def _market() -> dict:
    return {
        "title": 'Will Trump say "Iran" during events with Xi Jinping?',
        "category": "politics",
        "slug": "will-trump-say-iran-during-events-with-xi",
        "pulse_score": 72,
        "movement": 4,
        "volume": 200_000,
    }


def test_rss_adapter_parses_public_feed_items() -> None:
    xml = """
    <rss><channel>
      <item>
        <title>Bitcoin volatility returns</title>
        <link>https://example.com/bitcoin</link>
        <description>Crypto markets moved around short-term volatility.</description>
        <pubDate>Sat, 16 May 2026 10:00:00 GMT</pubDate>
      </item>
    </channel></rss>
    """
    source = SourceConfig(
        source_type="rss",
        name="Example Feed",
        url="https://example.com/rss.xml",
        category="crypto",
        credibility_score=70,
    )

    items = RSSAdapter.parse_feed(xml, source)

    assert len(items) == 1
    assert items[0].title == "Bitcoin volatility returns"
    assert items[0].category == "crypto"
    assert items[0].urgency_score > 25


def test_event_matching_links_market_to_related_news() -> None:
    matches = match_events_to_market(_market(), [_event()])

    assert matches
    assert matches[0].relevance_score >= 18
    assert "iran" in matches[0].match_reason or "trump" in matches[0].match_reason


def test_source_credibility_recognizes_official_sources() -> None:
    official = _event(source_type="official", source_name="Federal Reserve", credibility_score=94)
    social = _event(source_type="x", source_name="Public X", credibility_score=45)

    assert credibility_for_source(official) > credibility_for_source(social)
    assert news_confidence([official]) == "high"
    assert news_confidence([social]) == "low"


def test_duplicate_news_removed_by_url() -> None:
    first = _event(title="Original", credibility_score=60)
    second = _event(title="Updated", credibility_score=90)

    deduped = dedupe_events([first, second])

    assert len(deduped) == 1
    assert deduped[0].title == "Updated"


def test_market_gets_related_news_fields() -> None:
    context = build_news_context(_market(), [_event()], language="en")
    data = context.as_dict()

    assert data["latest_relevant_news"]
    assert data["source_count"] == 1
    assert data["credible_source_count"] == 1
    assert data["news_urgency"] == "high"
    assert data["why_moving_now"]


def test_unrelated_official_source_is_not_attached_to_market_news() -> None:
    market = {
        "title": "Will Carlos Álvarez win the 2026 Peruvian presidential election?",
        "category": "politics",
        "slug": "carlos-alvarez-peru-president-2026",
        "pulse_score": 82,
        "movement": 5,
        "volume": 300_000,
    }
    unrelated = ExternalNewsItem(
        source_type="official",
        source_name="White House Briefing Room",
        source_url="https://example.com/feed",
        title="Presidential Message on Armed Forces Day",
        summary="The message discusses military service and national recognition.",
        url="https://example.com/white-house",
        published_at=datetime(2026, 5, 16, tzinfo=timezone.utc),
        category="politics",
        entities=("trump", "iran"),
        topics=("military", "security"),
        urgency_score=90,
        credibility_score=95,
    )

    context = build_news_context(market, [unrelated], language="en")

    assert context.latest_relevant_news == ()
    assert context.related_news == ()
    assert context.official_source_signal is False
    assert context.confidence_from_news == "low"
    assert context.official_source_status == "No official source matched yet."


def test_stopword_only_overlap_does_not_create_related_news() -> None:
    market = {
        "title": "Who is known and the candidate in this election?",
        "category": "politics",
        "pulse_score": 75,
        "movement": 5,
        "volume": 200_000,
    }
    weak = ExternalNewsItem(
        source_type="rss",
        source_name="Example News",
        source_url="https://example.com/feed",
        title="Who is known and the latest public update",
        summary="The article uses generic wording without a direct entity.",
        url="https://example.com/weak",
        published_at=datetime(2026, 5, 16, tzinfo=timezone.utc),
        category="politics",
        entities=(),
        topics=(),
        urgency_score=80,
        credibility_score=80,
    )

    matches = match_events_to_market(market, [weak])
    context = build_news_context(market, [weak], language="en")

    assert matches == []
    assert context.latest_relevant_news == ()
    assert context.confidence_from_news == "low"


def test_match_reason_excludes_stopwords_from_terms() -> None:
    market = {"title": "Strait of Hormuz traffic returns", "category": "global"}
    event = ExternalNewsItem(
        source_type="rss",
        source_name="CNBC",
        source_url="https://example.com/feed",
        title="Global oil stockpiles if Strait of Hormuz remains closed",
        summary="Shipping traffic and oil context for the Strait of Hormuz.",
        url="https://example.com/hormuz",
        published_at=datetime(2026, 5, 16, tzinfo=timezone.utc),
        category="global",
        entities=(),
        topics=("shipping", "oil"),
        urgency_score=72,
        credibility_score=78,
    )
    matches = match_events_to_market(market, [event])

    assert matches
    terms = matched_terms_from_reason(matches[0].match_reason)
    assert {"strait", "hormuz"} <= set(terms)
    assert not {"and", "the", "who", "known"} & set(terms)


def test_official_source_increases_news_confidence() -> None:
    context = build_news_context(
        _market(),
        [_event(source_type="official", source_name="White House", credibility_score=95)],
        language="en",
    )

    assert context.official_source_signal is True
    assert context.confidence_from_news == "high"


def test_high_confidence_requires_market_relevance_not_source_quality_alone() -> None:
    market = {
        "title": "Will Carlos Álvarez win the 2026 Peruvian presidential election?",
        "category": "politics",
        "pulse_score": 90,
        "movement": 8,
        "volume": 1_000_000,
    }
    unrelated = _event(
        title="Federal Reserve announces bank supervision update",
        source_type="official",
        source_name="Federal Reserve",
        credibility_score=98,
    )

    context = build_news_context(market, [unrelated], language="en")

    assert context.official_source_signal is False
    assert context.confidence_from_news != "high"


def test_social_only_news_lowers_confidence() -> None:
    context = build_news_context(
        _market(),
        [_event(source_type="x", source_name="Public X", credibility_score=45)],
        language="en",
    )

    assert context.official_source_signal is False
    assert context.confidence_from_news == "low"


def test_news_context_has_no_financial_advice_language() -> None:
    text = " ".join(str(value).lower() for value in build_news_context(_market(), [_event()]).as_dict().values())

    for phrase in ("buy", "sell", "bet", "good bet", "guaranteed", "покупай", "продавай", "ставь"):
        assert phrase not in text


def test_news_engine_today_themes_fallback_and_seeded_events() -> None:
    empty_engine = NewsIntelligenceEngine(
        enable_rss=False,
        enable_official_sources=False,
        seed_events=[],
    )
    seeded_engine = NewsIntelligenceEngine(
        enable_rss=False,
        enable_official_sources=False,
        seed_events=[_event()],
    )

    assert empty_engine.today_themes([_market()])[0]["confidence"] == "low"
    assert seeded_engine.today_themes([_market()])[0]["theme"] == "Politics"
