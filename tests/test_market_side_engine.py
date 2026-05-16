from __future__ import annotations

from bot.services.market_side_engine import analyze_market_side


def test_probability_fallback_builds_yes_no_probabilities() -> None:
    side = analyze_market_side({"probability": 37, "volume": 120_000})

    assert side.yes_probability == 37
    assert side.no_probability == 63
    assert side.yes_price == 0.37
    assert side.no_price == 0.63
    assert side.side_confidence in {"low", "medium"}


def test_outcome_prices_are_used_when_available() -> None:
    side = analyze_market_side(
        {
            "outcomes": '["Yes","No"]',
            "outcomePrices": '["0.72","0.28"]',
            "volume": 180_000,
        },
        confirmation_level="strong",
    )

    assert side.yes_probability == 72
    assert side.no_probability == 28
    assert side.dominant_side == "YES"
    assert side.opposite_side == "NO"
    assert side.side_confidence in {"medium", "high"}


def test_dominant_no_and_extreme_no() -> None:
    side = analyze_market_side({"probability": 6, "volume": 100_000, "movement": 2})

    assert side.dominant_side == "NO"
    assert side.opposite_side == "YES"
    assert side.yes_probability == 6
    assert "NO" in side.side_balance
    assert side.side_tension
    assert side.side_verdict


def test_balanced_side() -> None:
    side = analyze_market_side({"probability": 51, "volume": 80_000})

    assert side.dominant_side == "BALANCED"
    assert side.side_confidence in {"low", "medium"}
    assert "close" in side.side_balance


def test_low_data_fallback() -> None:
    side = analyze_market_side({"title": "Unknown market"})

    assert side.dominant_side == "UNKNOWN"
    assert side.yes_probability is None
    assert side.no_probability is None
    assert side.side_summary == "Not enough side data yet."


def test_side_language_is_safe() -> None:
    side = analyze_market_side({"probability": 12, "volume": 150_000}, language="en")
    ru_side = analyze_market_side({"probability": 88, "volume": 150_000}, language="ru")
    text = " ".join(
        [
            side.side_summary,
            side.side_balance,
            side.side_tension,
            side.side_verdict,
            side.side_risk_note,
            ru_side.side_summary,
            ru_side.side_balance,
            ru_side.side_tension,
            ru_side.side_verdict,
            ru_side.side_risk_note,
        ]
    ).lower()

    for phrase in ("good bet", "guaranteed", "100%", "точный прогноз"):
        assert phrase not in text
    for phrase in ("b" + "uy", "se" + "ll", "be" + "t", "поку" + "пай", "прода" + "вай", "ста" + "вь"):
        assert phrase not in text


def test_yes_low_with_activity_mentions_opposite_interest() -> None:
    side = analyze_market_side({"probability": 8, "volume": 250_000, "movement": 2})

    assert side.dominant_side == "NO"
    assert side.opposite_interest in {"medium", "high"}
    assert "YES" in side.side_tension or "YES" in side.side_verdict
