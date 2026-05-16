from __future__ import annotations

import json

import pytest

from bot.services.ai_context_engine import AIContextEngine
from bot.services.ai_output_parser import (
    detect_banned_language,
    detect_generic_phrases,
    extract_json_from_text,
    parse_ai_json_response,
)
from bot.services.ai_output_schema import fallback_for_language, market_insight_schema, today_narrative_schema


def _valid_market_payload() -> dict:
    payload = fallback_for_language(market_insight_schema, "en")
    payload.update(
        {
            "quick_take": "Bitcoin repricing looks cautious because volume is not broad enough yet.",
            "main_tension": "Visibility is higher than the strength of confirmation.",
            "what_this_means": "This is best read as a context check, not a firm repricing.",
            "attention_vs_conviction": "Expectations look mostly stable while the market gets more visible.",
            "related_topics": ["Bitcoin", "Crypto volatility"],
        }
    )
    return payload


def test_parses_clean_json() -> None:
    result = parse_ai_json_response(json.dumps(_valid_market_payload()), market_insight_schema)

    assert result.ok is True
    assert result.payload["quick_take"].startswith("Bitcoin")


def test_parses_json_in_markdown_code_block() -> None:
    raw = "```json\n" + json.dumps(_valid_market_payload()) + "\n```"

    result = parse_ai_json_response(raw, market_insight_schema)

    assert result.ok is True
    assert result.payload["related_topics"] == ["Bitcoin", "Crypto volatility"]


def test_extracts_json_from_text_wrapper_and_repairs_trailing_comma() -> None:
    raw = 'Here is the JSON:\n{"headline":"Brief","what_changed":["A"],"category_summaries":{},"interpretation":"Readable.",}'

    result = parse_ai_json_response(raw, today_narrative_schema)

    assert result.ok is True
    assert result.payload["headline"] == "Brief"
    assert extract_json_from_text(raw).startswith("{")


def test_rejects_missing_required_fields() -> None:
    result = parse_ai_json_response('{"quick_take":"Only one field"}', market_insight_schema)

    assert result.ok is False
    assert any(error.startswith("missing:") for error in result.errors)
    assert result.payload["what_this_means"]


def test_detects_banned_advice_language() -> None:
    phrase = "please " + "b" + "uy"

    assert detect_banned_language({"text": phrase}) == ["b" + "uy"]
    result = parse_ai_json_response(json.dumps({**_valid_market_payload(), "quick_take": phrase}), market_insight_schema)
    assert result.ok is False
    assert "banned_language" in result.errors


def test_detects_generic_phrases() -> None:
    text = "People are watching this market."

    assert detect_generic_phrases({"text": text}) == ["people are watching"]
    result = parse_ai_json_response(json.dumps({**_valid_market_payload(), "quick_take": text}), market_insight_schema)
    assert result.ok is False
    assert "generic_phrase" in result.errors


class _RetryEngine(AIContextEngine):
    def __init__(self, responses: list[str]) -> None:
        super().__init__("test-key")
        self.responses = responses
        self.calls = 0

    async def _openai_chat_content(self, payload):  # type: ignore[no-untyped-def]
        self.calls += 1
        return self.responses.pop(0)


@pytest.mark.asyncio
async def test_retries_once_on_invalid_json() -> None:
    valid = json.dumps(
        {
            "headline": "Crypto is the clearest theme today.",
            "what_changed": ["Crypto markets became more visible"],
            "category_summaries": {"crypto": "Short-term crypto markets are carrying the read."},
            "interpretation": "The read is concentrated rather than broad.",
        }
    )
    engine = _RetryEngine(["{bad json", valid])

    result = await engine._complete_json(
        "Return today JSON",
        schema=today_narrative_schema,
        response_type="today_narrative",
    )

    assert result is not None
    assert result["headline"].startswith("Crypto")
    assert engine.calls == 2
    assert engine.quality_stats()["ai_parse_error_count"] == 1
    assert engine.quality_stats()["ai_fallback_count"] == 0


@pytest.mark.asyncio
async def test_falls_back_after_failed_retry() -> None:
    engine = _RetryEngine(["{bad json", "{still bad"])

    result = await engine._complete_json(
        "Return today JSON",
        schema=today_narrative_schema,
        response_type="today_narrative",
    )

    assert result is None
    assert engine.calls == 2
    assert engine.quality_stats()["ai_parse_error_count"] == 2
    assert engine.quality_stats()["ai_fallback_count"] == 1
