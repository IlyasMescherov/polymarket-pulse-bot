from __future__ import annotations

from datetime import datetime, timezone

from bot.services.market_side_engine import analyze_market_side
from bot.services.outcome_normalizer import normalize_market_outcomes
from bot.services.polymarket_client import Market
from bot.utils.formatting import format_market_card


def test_yes_no_outcomes_detected_as_binary_yes_no() -> None:
    result = normalize_market_outcomes(
        {"outcomes": '["Yes","No"]', "outcomePrices": '["0.23","0.77"]'}
    )

    assert result.outcome_type == "binary_yes_no"
    assert result.should_use_yes_no is True
    assert result.display_outcomes[0]["short_label"] == "YES"
    assert result.display_outcomes[1]["short_label"] == "NO"


def test_two_custom_outcomes_detected_as_binary_custom() -> None:
    result = normalize_market_outcomes(
        {"outcomes": '["Over","Under"]', "outcomePrices": '["0.41","0.59"]'}
    )

    assert result.outcome_type == "binary_custom"
    assert result.should_use_yes_no is False
    assert result.dominant_outcome_label == "Under"


def test_three_event_outcomes_detected_as_sports_moneyline() -> None:
    result = normalize_market_outcomes(
        {
            "question": "Will Stuttgart win?",
            "events": [
                {
                    "title": "Eintracht Frankfurt vs. VfB Stuttgart",
                    "slug": "frankfurt-stuttgart",
                    "markets": [
                        {
                            "groupItemTitle": "Frankfurt",
                            "outcomes": '["Yes","No"]',
                            "outcomePrices": '["0.025","0.975"]',
                        },
                        {
                            "groupItemTitle": "Draw",
                            "outcomes": '["Yes","No"]',
                            "outcomePrices": '["0.08","0.92"]',
                        },
                        {
                            "groupItemTitle": "Stuttgart",
                            "outcomes": '["Yes","No"]',
                            "outcomePrices": '["0.895","0.105"]',
                        },
                    ],
                }
            ],
        }
    )

    assert result.outcome_type == "sports_moneyline"
    assert result.should_use_yes_no is False
    assert [item["short_label"] for item in result.display_outcomes] == [
        "Frankfurt",
        "Draw",
        "Stuttgart",
    ]
    assert result.dominant_outcome_label == "Stuttgart"


def test_more_than_three_outcomes_detected_as_multi_outcome() -> None:
    result = normalize_market_outcomes(
        {
            "outcomes": '["A","B","C","D"]',
            "outcomePrices": '["0.33","0.22","0.2","0.1"]',
        }
    )

    assert result.outcome_type == "multi_outcome"
    assert result.should_use_yes_no is False
    assert len(result.display_outcomes) == 4


def test_missing_outcomes_fallback_for_will_question() -> None:
    result = normalize_market_outcomes({"title": "Will Bitcoin hit $150k?", "probability": 12})

    assert result.outcome_type == "binary_yes_no"
    assert result.should_use_yes_no is True
    assert result.display_outcomes[0]["probability"] == 12


def test_should_use_yes_no_false_for_team_market() -> None:
    side = analyze_market_side(
        {
            "question": "Will Chelsea FC win on 2026-05-16?",
            "events": [
                {
                    "title": "Chelsea FC vs. Manchester City FC",
                    "markets": [
                        {
                            "groupItemTitle": "Chelsea FC",
                            "outcomes": '["Yes","No"]',
                            "outcomePrices": '["0.185","0.815"]',
                        },
                        {
                            "groupItemTitle": "Draw",
                            "outcomes": '["Yes","No"]',
                            "outcomePrices": '["0.345","0.655"]',
                        },
                        {
                            "groupItemTitle": "Manchester City FC",
                            "outcomes": '["Yes","No"]',
                            "outcomePrices": '["0.475","0.525"]',
                        },
                    ],
                }
            ],
            "volume": 7_000_000,
        },
        language="en",
    )

    assert side.should_use_yes_no is False
    assert side.outcome_type == "sports_moneyline"
    assert side.dominant_outcome_label == "Manchester City FC"
    assert "YES" not in side.outcome_balance_summary
    assert "NO" not in side.outcome_balance_summary


def test_telegram_card_renders_real_outcome_labels_for_custom_market() -> None:
    market = Market(
        id="sports-1",
        question="Will Chelsea FC win on 2026-05-16?",
        slug="chelsea-city",
        yes_probability=0.185,
        volume=7_000_000,
        end_date=datetime(2026, 5, 16, tzinfo=timezone.utc),
        url="https://polymarket.com/event/chelsea-city",
        raw={
            "events": [
                {
                    "title": "Chelsea FC vs. Manchester City FC",
                    "markets": [
                        {
                            "groupItemTitle": "Chelsea FC",
                            "outcomes": '["Yes","No"]',
                            "outcomePrices": '["0.185","0.815"]',
                        },
                        {
                            "groupItemTitle": "Draw",
                            "outcomes": '["Yes","No"]',
                            "outcomePrices": '["0.345","0.655"]',
                        },
                        {
                            "groupItemTitle": "Manchester City FC",
                            "outcomes": '["Yes","No"]',
                            "outcomePrices": '["0.475","0.525"]',
                        },
                    ],
                }
            ]
        },
    )

    card = format_market_card(market, language="en")

    assert "Market outcomes:" in card
    assert "Chelsea FC: 18.5%" in card
    assert "Draw: 34.5%" in card
    assert "Manchester City FC: 47.5%" in card
    assert "YES:" not in card
    assert "NO:" not in card


def test_no_direct_action_language_in_outcome_text() -> None:
    side = analyze_market_side(
        {"outcomes": '["Frankfurt","Draw","Stuttgart"]', "outcomePrices": '["0.025","0.08","0.895"]'}
    )
    text = " ".join(
        [
            side.outcome_balance_summary,
            side.side_tension,
            side.side_verdict,
            side.side_risk_note,
        ]
    ).lower()

    for phrase in ("good bet", "guaranteed", "100%", "insider", "alpha leak"):
        assert phrase not in text
    for phrase in ("b" + "uy", "se" + "ll", "be" + "t"):
        assert phrase not in text
