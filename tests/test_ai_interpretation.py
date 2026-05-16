from __future__ import annotations

from datetime import datetime, timedelta, timezone

from bot.services.ai_insight_engine import (
    classify_attention_vs_conviction,
    classify_insight_strength,
    classify_movement_strength,
    detect_main_tension,
    detect_resolution_proximity,
    detect_speculative_attention,
    generate_market_briefing,
    generate_today_narrative,
    generate_what_changed,
    generate_what_this_means,
    humanize_pulse_score,
)
from bot.services.ai_prompts import (
    build_market_briefing_prompt,
    build_today_narrative_prompt,
    build_what_changed_prompt,
    validate_ai_output,
)
from bot.services.category_analyzer import category_summary, get_category_prompt_modifier
from bot.services.cross_market_analyzer import detect_divergence, group_markets_by_narrative


def _market(**overrides: object) -> dict:
    base = {
        "id": "m1",
        "title": "Will Bitcoin hit $150k by December 31, 2026?",
        "category": "crypto",
        "probability": 42,
        "probability_delta": 1.0,
        "volume": 150_000,
        "end_date": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
    }
    base.update(overrides)
    return base


def _assert_safe(text: str) -> None:
    assert validate_ai_output(text) == []


def test_no_banned_phrases() -> None:
    market = _market(volume=200_000, probability_delta=1)
    outputs = [
        classify_attention_vs_conviction(market)["interpretation"],
        generate_what_this_means(market),
        generate_today_narrative([market]),
        *generate_what_changed([market]),
    ]

    for output in outputs:
        _assert_safe(output)


def test_no_legacy_jargon_wording() -> None:
    text = " ".join(
        [
            classify_attention_vs_conviction(_market())["interpretation"],
            generate_what_this_means(_market()),
            generate_market_briefing(_market())["attention_vs_conviction"],  # type: ignore[index]
        ]
    ).lower()

    for phrase in ("sig" + "nal", "noi" + "se", "ш" + "ум", "сиг" + "нал"):
        assert phrase not in text


def test_no_financial_advice_language() -> None:
    briefing = generate_market_briefing(_market(probability_delta=8, volume=250_000))
    combined = " ".join(str(value) for value in briefing.values()).lower()

    for phrase in ("b" + "uy", "se" + "ll", "good " + "bet", "guaran" + "teed", "100" + "%"):
        assert phrase not in combined


def test_explain_has_required_sections() -> None:
    briefing = generate_market_briefing(_market(probability_delta=6, volume=250_000))

    for key in (
        "quick_take",
        "what_happened",
        "what_is_happening",
        "main_tension",
        "what_this_means",
        "attention_vs_conviction",
        "insight_strength",
        "confidence_level",
        "strength_of_read",
        "how_strong_is_the_move",
        "what_to_check",
        "related_topics",
        "resolution_note",
        "category_voice",
    ):
        assert briefing[key]
    assert briefing["what_this_means"] != briefing["what_happened"]


def test_weak_data_fallback_not_empty() -> None:
    market = _market(volume=200, probability_delta=0)

    assert generate_what_this_means(market)
    assert generate_today_narrative([])
    assert generate_market_briefing(market)["quick_take"]


def test_category_summaries_differ() -> None:
    politics = category_summary("politics", "en")
    crypto = category_summary("crypto", "en")
    sports = category_summary("sports", "en")

    assert politics != crypto
    assert crypto != sports
    assert get_category_prompt_modifier("politics", "en") != get_category_prompt_modifier("sports", "en")


def test_cross_market_grouping() -> None:
    markets = [
        _market(id="btc-1", title="Will Bitcoin hit $150k by June?", probability_delta=3),
        _market(id="btc-2", title="Will BTC reach a new all time high?", probability_delta=2),
        _market(id="sports-1", title="Will the Lakers win tonight?", category="sports"),
    ]

    groups = group_markets_by_narrative(markets)

    assert groups
    assert groups[0]["narrative"] == "Bitcoin volatility"
    assert groups[0]["group_interpretation"]


def test_pulse_score_humanized() -> None:
    assert humanize_pulse_score(12, "en") == "Quiet"
    assert humanize_pulse_score(57, "en") == "Attention rising"
    assert humanize_pulse_score(57, "ru") == "Рынок заметнее"
    assert "/" not in humanize_pulse_score(57, "en")


def test_no_mixed_language() -> None:
    ru_text = generate_what_this_means(_market(volume=150_000, probability_delta=1), "ru")
    en_text = generate_what_this_means(_market(volume=150_000, probability_delta=1), "en")

    assert any("а" <= char.lower() <= "я" or char.lower() == "ё" for char in ru_text)
    assert not any("а" <= char.lower() <= "я" or char.lower() == "ё" for char in en_text)


def test_attention_vs_conviction_classification() -> None:
    attention = classify_attention_vs_conviction(_market(volume=300_000, probability_delta=1), "en")
    conviction = classify_attention_vs_conviction(_market(volume=5_000, probability_delta=8), "en")
    both = classify_attention_vs_conviction(_market(volume=300_000, probability_delta=8), "en")

    assert attention["attention_level"] == "high"
    assert attention["conviction_level"] == "low"
    assert conviction["attention_level"] == "low"
    assert conviction["conviction_level"] == "medium"
    assert both["attention_level"] == "high"
    assert both["conviction_level"] == "high"


def test_contradiction_detection_activity_flat_probability() -> None:
    text = detect_main_tension(_market(volume=300_000, probability_delta=1), "en")
    assert "expectations did not move" in text


def test_contradiction_detection_probability_move_weak_volume() -> None:
    text = detect_main_tension(_market(volume=5_000, probability_delta=8), "en")
    assert "volume is weak" in text.lower()


def test_insight_strength_scale() -> None:
    weak = classify_insight_strength(_market(volume=1_000, probability_delta=0), "en")
    attention = classify_insight_strength(_market(volume=300_000, probability_delta=1), "en")
    stronger = classify_insight_strength(_market(volume=300_000, probability_delta=7, pulse_score=80), "en")

    assert weak["label"] == "Weak confirmation"
    assert attention["label"] == "Interest is present"
    assert stronger["label"] in {"More noticeable than usual", "More convincing than usual"}


def test_resolution_and_speculative_attention_helpers() -> None:
    soon = _market(end_date=(datetime.now(timezone.utc) + timedelta(hours=4)).isoformat())
    assert detect_resolution_proximity(soon)
    assert detect_speculative_attention(_market(volume=250_000, probability_delta=1))
    assert classify_movement_strength(_market(volume=1_000, probability_delta=0)) == "quiet"


def test_prompt_templates_and_validation() -> None:
    market = _market()
    prompts = [
        build_market_briefing_prompt(market, "en"),
        build_today_narrative_prompt([market], "en"),
        build_what_changed_prompt([market], "en"),
    ]

    assert all("Output language: English" in prompt for prompt in prompts)
    assert validate_ai_output("This text is calm.") == []
    assert validate_ai_output("please " + "b" + "uy")[0] == "b" + "uy"


def test_cross_market_divergence() -> None:
    group = {
        "narrative": "Bitcoin volatility",
        "markets": [
            _market(id="a", probability_delta=4),
            _market(id="b", probability_delta=-3),
        ],
    }
    assert detect_divergence(group)
