from __future__ import annotations

import httpx
import pytest

from bot.services.polymarket_client import parse_market
from bot.services.polymarket_client import PolymarketClient


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


@pytest.mark.asyncio
async def test_client_enriches_grouped_event_outcomes() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/markets":
            return httpx.Response(
                200,
                json=[
                    {
                        "id": "m1",
                        "question": "Will Manchester City FC win on 2026-05-16?",
                        "slug": "mnc-win",
                        "groupItemTitle": "Manchester City FC",
                        "outcomes": '["Yes","No"]',
                        "outcomePrices": '["0.475","0.525"]',
                        "events": [{"slug": "chelsea-manchester-city", "title": "Chelsea FC vs. Manchester City FC"}],
                    }
                ],
            )
        if request.url.path == "/events":
            return httpx.Response(
                200,
                json=[
                    {
                        "slug": "chelsea-manchester-city",
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
            )
        return httpx.Response(404)

    async with httpx.AsyncClient(
        base_url="https://gamma-api.polymarket.com",
        transport=httpx.MockTransport(handler),
    ) as client:
        polymarket = PolymarketClient("https://gamma-api.polymarket.com", client=client)
        markets = await polymarket.fetch_hot_markets(limit=1)

    assert markets[0].raw["eventSlug"] == "chelsea-manchester-city"
    assert len(markets[0].raw["eventMarkets"]) == 3
