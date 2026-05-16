from __future__ import annotations

import json

from bot.services.ai_output_parser import parse_ai_json_response, sanitize_ai_text, validate_required_fields
from bot.services.ai_output_schema import (
    fallback_for_language,
    market_insight_schema,
    schema_prompt,
    today_narrative_schema,
)


def test_market_schema_has_required_critical_fields() -> None:
    assert "quick_take" in market_insight_schema.required_fields
    assert "what_this_means" in market_insight_schema.critical_fields
    assert "attention_vs_conviction" in market_insight_schema.critical_fields


def test_schema_prompt_describes_required_fields() -> None:
    prompt = schema_prompt(today_narrative_schema)

    assert "today_narrative" in prompt
    assert "headline" in prompt
    assert "critical_non_empty" in prompt


def test_required_field_validator_rejects_empty_critical_field() -> None:
    payload = fallback_for_language(market_insight_schema, "en")
    payload["what_this_means"] = ""

    errors = validate_required_fields(payload, market_insight_schema)

    assert "empty:what_this_means" in errors


def test_sanitize_truncates_long_text() -> None:
    payload = fallback_for_language(market_insight_schema, "en")
    payload["quick_take"] = "A" * 400

    sanitized = sanitize_ai_text(payload, market_insight_schema)

    assert len(sanitized["quick_take"]) <= market_insight_schema.max_lengths["quick_take"]


def test_ru_fallback_uses_ru_copy() -> None:
    fallback = fallback_for_language(today_narrative_schema, "ru")

    assert "Сегодня" in fallback["headline"]


def test_api_still_responds_when_openai_returns_invalid_json_shape() -> None:
    result = parse_ai_json_response(
        json.dumps({"headline": "", "what_changed": "wrong", "category_summaries": [], "interpretation": ""}),
        today_narrative_schema,
    )

    assert result.ok is False
    assert result.payload["headline"]
