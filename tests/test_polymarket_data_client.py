from __future__ import annotations

import httpx
import pytest

from bot.services.polymarket_data_client import PolymarketDataClient


@pytest.mark.asyncio
async def test_data_client_parses_trades_leaderboard_and_positions() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/trades":
            return httpx.Response(
                200,
                json={
                    "data": [
                        {
                            "marketId": "m1",
                            "marketTitle": "Will bitcoin move?",
                            "wallet": "0x1111111111111111111111111111111111111111",
                            "amount": "25000",
                            "price": "0.5",
                            "size": "50000",
                        }
                    ]
                },
            )
        if request.url.path == "/v1/leaderboard":
            return httpx.Response(
                200,
                json={
                    "data": [
                        {
                            "wallet": "0x2222222222222222222222222222222222222222",
                            "volume": "100000",
                            "trades": 12,
                            "rank": 1,
                        }
                    ]
                },
            )
        if request.url.path == "/positions":
            return httpx.Response(
                200,
                json={
                    "data": [
                        {
                            "marketId": "m2",
                            "marketTitle": "Will ETH move?",
                            "size": "10",
                            "currentValue": "100",
                        }
                    ]
                },
            )
        return httpx.Response(404)

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="https://data-api.polymarket.com",
    ) as client:
        data_client = PolymarketDataClient("https://data-api.polymarket.com", client=client)
        trades = await data_client.get_trades()
        traders = await data_client.get_leaderboard()
        positions = await data_client.get_positions("0x2222222222222222222222222222222222222222")

    assert trades[0].market_id == "m1"
    assert trades[0].amount_usd == 25000
    assert traders[0].volume == 100000
    assert positions[0].market_title == "Will ETH move?"


@pytest.mark.asyncio
async def test_data_client_gracefully_falls_back_on_api_errors() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"error": "blocked"})

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="https://data-api.polymarket.com",
    ) as client:
        data_client = PolymarketDataClient("https://data-api.polymarket.com", client=client)
        assert await data_client.get_trades() == []
        assert await data_client.get_leaderboard() == []
        assert await data_client.get_positions("0x2222222222222222222222222222222222222222") == []
