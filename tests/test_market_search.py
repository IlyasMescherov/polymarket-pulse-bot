from __future__ import annotations

import httpx
import pytest

from bot.services.market_analyzer import MarketAnalyzer
from bot.services.polymarket_client import PolymarketClient


def _response(payload: object, status_code: int = 200) -> httpx.Response:
    request = httpx.Request("GET", "https://gamma-api.polymarket.com/test")
    return httpx.Response(status_code, json=payload, request=request)


@pytest.mark.asyncio
async def test_search_uses_public_search_before_fallback() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/public-search":
            return _response(
                {
                    "markets": [
                        {
                            "id": "1",
                            "question": "Will Bitcoin hit $100k?",
                            "slug": "bitcoin-100k",
                            "outcomes": '["Yes","No"]',
                            "outcomePrices": '["0.5","0.5"]',
                        }
                    ]
                }
            )
        return _response([])

    client = httpx.AsyncClient(
        base_url="https://gamma-api.polymarket.com",
        transport=httpx.MockTransport(handler),
    )
    analyzer = MarketAnalyzer(PolymarketClient("https://gamma-api.polymarket.com", client=client))

    markets = await analyzer.search_markets("bitcoin", limit=5)

    assert [market.id for market in markets] == ["1"]
    await client.aclose()


@pytest.mark.asyncio
async def test_search_falls_back_to_active_markets() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/public-search":
            return _response({"results": []}, status_code=404)
        return _response(
            [
                {
                    "id": "2",
                    "question": "Will OpenAI release a model?",
                    "slug": "openai-model",
                    "outcomes": '["Yes","No"]',
                    "outcomePrices": '["0.3","0.7"]',
                }
            ]
        )

    client = httpx.AsyncClient(
        base_url="https://gamma-api.polymarket.com",
        transport=httpx.MockTransport(handler),
    )
    analyzer = MarketAnalyzer(PolymarketClient("https://gamma-api.polymarket.com", client=client))

    markets = await analyzer.search_markets("openai", limit=5)

    assert [market.id for market in markets] == ["2"]
    await client.aclose()
