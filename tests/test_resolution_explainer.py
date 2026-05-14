from __future__ import annotations

from datetime import datetime, timezone

from bot.services.polymarket_client import Market
from bot.services.resolution_explainer import (
    build_resolution_explanation,
    extract_resolution_fields,
)


def test_resolution_explainer_uses_market_rules() -> None:
    market = Market(
        id="1",
        question="Will CPI be above 3%?",
        slug=None,
        yes_probability=0.42,
        volume=50_000,
        end_date=datetime(2026, 6, 1, tzinfo=timezone.utc),
        url="https://polymarket.com",
        raw={
            "description": "Resolves Yes if official CPI is above 3%.",
            "rules": "Use the official BLS release.",
            "resolutionSource": "BLS",
        },
    )

    fields = extract_resolution_fields(market)
    explanation = build_resolution_explanation(market)

    assert fields.resolution_source == "BLS"
    assert "official CPI" in explanation
    assert "BLS" in explanation
    assert "это текущая оценка рынка" in explanation


def test_resolution_explainer_falls_back_safely() -> None:
    market = Market(
        id="1",
        question="Will something happen?",
        slug=None,
        yes_probability=None,
        volume=None,
        end_date=None,
        url="https://polymarket.com",
        raw={},
    )

    explanation = build_resolution_explanation(market)

    assert "проверь правила разрешения" in explanation.lower()
    assert "данных пока нет" in explanation
