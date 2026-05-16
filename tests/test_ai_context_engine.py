from __future__ import annotations

from datetime import datetime, timezone

import pytest

from bot.services.ai_context_engine import AIContextEngine
from bot.services.market_mood import calculate_market_mood
from bot.services.polymarket_client import Market
from bot.services.pulse_score import calculate_pulse_score


def _market(probability: float | None = 0.63) -> Market:
    return Market(
        id="m1",
        question="Will Bitcoin hit $150k by December 31, 2026?",
        slug="will-bitcoin-hit-150k-by-december-31-2026",
        yes_probability=probability,
        volume=125_000,
        end_date=datetime(2026, 12, 31, tzinfo=timezone.utc),
        url="https://polymarket.com/market/will-bitcoin-hit-150k-by-december-31-2026",
        raw={"description": "Bitcoin price market", "tags": ["crypto", "bitcoin"]},
    )


@pytest.mark.asyncio
async def test_ai_context_engine_fallback_works_without_api_key() -> None:
    market = _market()
    pulse = calculate_pulse_score(market, delta=0.04)
    mood = calculate_market_mood(market, delta=0.04, language="en")

    context = await AIContextEngine(None).market_context(
        market,
        pulse,
        mood,
        delta=0.04,
        language="en",
    )

    assert context.why_people_care
    assert context.simple_read
    assert context.what_to_watch
    assert context.what_this_means
    assert context.quick_take
    assert context.what_happened
    assert context.main_tension
    assert context.insight_strength in {
        "Weak confirmation",
        "Interest is present",
        "More noticeable than usual",
        "Strong attention",
        "More convincing than usual",
    }
    assert context.confidence_level
    assert context.resolution_note
    assert context.category_voice
    assert context.market_memory_summary
    assert context.market_regime
    assert context.market_regime_key
    assert context.regime_reason
    assert context.memory_pattern
    assert context.changed_since_last_seen
    assert context.historical_context
    assert context.attention_vs_conviction
    assert context.related_topics
    assert context.category == "crypto"
    assert context.probability_interpretation == "Likely"
    assert len(context.why_people_care) <= 140
    assert context.why_people_care == "Crypto volatility made this market more visible."
    assert "People are watching because activity increased" not in context.why_people_care
    assert "Attention" in context.attention_vs_conviction or "expectations" in context.attention_vs_conviction


@pytest.mark.asyncio
async def test_ai_context_engine_uses_market_memory_history() -> None:
    market = _market(probability=0.42)
    pulse = calculate_pulse_score(market, delta=0.005)
    mood = calculate_market_mood(market, delta=0.005, language="en")

    class Snapshot:
        yes_probability = 0.415
        volume = 90_000
        end_date = market.end_date

    context = await AIContextEngine(None).market_context(
        market,
        pulse,
        mood,
        delta=0.005,
        language="en",
        history=[Snapshot()],
    )

    assert context.market_memory_summary != "Not enough history for comparison yet."
    assert context.market_regime_key in {"short_term_attention", "active", "sustained_interest"}


@pytest.mark.asyncio
async def test_ai_daily_narrative_fallback_is_short_and_safe() -> None:
    market = _market()
    pulse = calculate_pulse_score(market)
    mood = calculate_market_mood(market, language="en")
    engine = AIContextEngine(None)
    context = await engine.market_context(market, pulse, mood, language="en")

    narrative = await engine.daily_narrative([market], [context], language="en")
    combined = " ".join([narrative.headline, *narrative.what_changed, *narrative.category_summaries.values()]).lower()

    assert narrative.headline
    assert narrative.interpretation
    assert narrative.what_changed
    assert any("Crypto" in item or "activity" in item for item in narrative.what_changed)
    assert all(len(item) <= 160 for item in narrative.what_changed)
    assert "expectations" in narrative.interpretation or "attention" in narrative.interpretation
    for fragment in ("buy " + "now", "sell " + "now", "trade " + "signal", "guaran" + "teed"):
        assert fragment not in combined


def test_probability_humanization_en_and_ru() -> None:
    engine = AIContextEngine(None)

    assert engine.probability_interpretation(0.004, "en") == "Unlikely"
    assert engine.probability_interpretation(0.2, "en") == "Possible"
    assert engine.probability_interpretation(0.55, "en") == "Likely"
    assert engine.probability_interpretation(0.82, "en") == "Highly likely"
    assert engine.probability_interpretation(0.004, "ru") == "Маловероятно"
    assert engine.probability_interpretation(0.82, "ru") == "Очень вероятно"


@pytest.mark.asyncio
async def test_ai_context_engine_treats_music_award_as_culture() -> None:
    market = Market(
        id="award",
        question="Will a local music award happen this month?",
        slug="local-music-award",
        yes_probability=0.34,
        volume=25_000,
        end_date=datetime(2026, 12, 31, tzinfo=timezone.utc),
        url="https://polymarket.com/market/local-music-award",
        raw={"category": "Culture", "description": "Local entertainment and music event"},
    )
    pulse = calculate_pulse_score(market, delta=0.01)
    mood = calculate_market_mood(market, delta=0.01, language="en")

    context = await AIContextEngine(None).market_context(
        market,
        pulse,
        mood,
        delta=0.01,
        language="en",
    )

    assert context.category == "culture"
    assert "Culture" in context.related_topics
    assert "Geopolitics" not in context.related_topics
    assert "Political headlines" not in context.why_people_care


@pytest.mark.asyncio
async def test_attention_vs_conviction_distinguishes_attention_from_expectations() -> None:
    market = _market(probability=0.1)
    pulse = calculate_pulse_score(market, delta=0.0)
    mood = calculate_market_mood(market, delta=0.0, language="en")

    context = await AIContextEngine(None).market_context(
        market,
        pulse,
        mood,
        delta=0.0,
        language="en",
    )

    assert context.what_this_means
    assert context.insight_strength in {"Interest is present", "Strong attention"}
    assert "expectations" in context.attention_vs_conviction
    assert "buy" not in context.what_this_means.lower()


@pytest.mark.asyncio
async def test_share_snapshot_is_safe_and_points_to_app() -> None:
    market = _market()
    engine = AIContextEngine(None)
    context = await engine.market_context(
        market,
        calculate_pulse_score(market),
        calculate_market_mood(market, language="en"),
        language="en",
    )
    text = engine.share_snapshot([market], [context], language="en")

    assert "Today’s Pulse" in text
    assert "Open PulseMarket AI" in text
    assert "https://app.pulsemarketai.com/app" in text
    assert "financial advice" not in text.lower()
