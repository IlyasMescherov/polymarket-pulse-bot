from __future__ import annotations

from bot.services.ai_output_schema import fallback_for_language, market_insight_schema
from bot.services.ai_quality_engine import fallback_interpretation, score_ai_output


def test_quality_score_rewards_specific_context() -> None:
    payload = fallback_for_language(market_insight_schema, "en")
    payload["quick_take"] = "Bitcoin volatility is visible, but expectations look mostly stable."
    payload["what_this_means"] = "The Bitcoin read is concentrated in short-term context, not broad repricing."

    result = score_ai_output(payload, schema=market_insight_schema, context={"title": "Will Bitcoin hit $150k?"})

    assert result.score >= 80
    assert "generic_phrase" not in result.flags


def test_quality_score_flags_generic_phrases() -> None:
    payload = fallback_for_language(market_insight_schema, "en")
    payload["quick_take"] = "Interest is there, confidence is limited."

    result = score_ai_output(payload, schema=market_insight_schema)

    assert result.score < 80
    assert "generic_phrase" in result.flags


def test_quality_score_flags_unsafe_advice() -> None:
    payload = fallback_for_language(market_insight_schema, "en")
    payload["quick_take"] = "Please " + "b" + "uy now."

    result = score_ai_output(payload, schema=market_insight_schema)

    assert result.score <= 20
    assert "banned_language" in result.flags


def test_fallback_copy_is_not_generic() -> None:
    text = fallback_interpretation(probability_moved=True, news_exists=True)
    generic = ("people are watching", "activity increased", "worth watching", "could be important")

    assert text
    assert all(phrase not in text.lower() for phrase in generic)


def test_fallback_copy_handles_multi_outcome() -> None:
    text = fallback_interpretation(dominant_outcome="Stuttgart", runner_up="Draw")

    assert "Stuttgart" in text
    assert "Draw" in text
