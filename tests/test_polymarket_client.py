from __future__ import annotations

from bot.services.polymarket_client import parse_market


def test_parse_market_reads_yes_probability_from_json_strings() -> None:
    market = parse_market(
        {
            "id": "540817",
            "question": "New Rihanna Album before GTA VI?",
            "slug": "new-rhianna-album-before-gta-vi-926",
            "outcomes": '["Yes", "No"]',
            "outcomePrices": '["0.52", "0.48"]',
            "volumeNum": 723226.86,
            "endDate": "2026-07-31T12:00:00Z",
        }
    )

    assert market is not None
    assert market.yes_probability == 0.52
    assert market.volume == 723226.86
    assert market.end_date is not None
    assert market.url.endswith("/new-rhianna-album-before-gta-vi-926")


def test_parse_market_uses_first_outcome_when_yes_is_missing() -> None:
    market = parse_market(
        {
            "id": "1",
            "question": "Bitcoin Up or Down?",
            "slug": "bitcoin-up-or-down",
            "outcomes": '["Up", "Down"]',
            "outcomePrices": '["0.44", "0.56"]',
        }
    )

    assert market is not None
    assert market.yes_probability == 0.44


def test_parse_market_handles_missing_prices() -> None:
    market = parse_market(
        {
            "id": "1",
            "question": "Market without prices",
            "slug": "market-without-prices",
            "outcomes": '["Yes", "No"]',
        }
    )

    assert market is not None
    assert market.yes_probability is None

