from __future__ import annotations

import logging

import httpx

from bot.services.polymarket_client import Market

logger = logging.getLogger(__name__)


class AIExplainer:
    def __init__(
        self,
        api_key: str | None,
        model: str = "gpt-4o-mini",
        timeout: float = 12.0,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._timeout = timeout

    @property
    def enabled(self) -> bool:
        return bool(self._api_key)

    async def explain_market(self, market: Market) -> str | None:
        if not self._api_key:
            return None

        prompt = (
            "Explain this Polymarket prediction market for a beginner in Russian. "
            "Keep it under 3 short bullet points. Do not give financial advice. "
            "Focus on why it may be interesting, what could influence it, and what to watch.\n\n"
            f"Market: {market.question}\n"
            f"Probability: {market.yes_probability}\n"
            f"Volume: {market.volume}\n"
            f"Ends: {market.end_date}\n"
        )
        payload = {
            "model": self._model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a concise analyst for a Telegram bot. "
                        "Use plain Russian and avoid trading instructions."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 180,
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("OpenAI explanation failed: %s", exc)
            return None

        try:
            content = data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError, AttributeError):
            logger.warning("Unexpected OpenAI response shape")
            return None

        return content or None

    async def explain_resolution(self, market: Market) -> str | None:
        if not self._api_key:
            return None

        prompt = (
            "Explain how this Polymarket market is likely resolved for a beginner in Russian. "
            "Use exactly 4 short bullet points. Do not give financial advice or trading advice.\n\n"
            f"Market: {market.question}\n"
            f"Description: {market.raw.get('description')}\n"
            f"Rules: {market.raw.get('rules')}\n"
            f"Resolution source: {market.raw.get('resolutionSource') or market.raw.get('resolution_source')}\n"
            f"Ends: {market.end_date}\n"
        )
        payload = {
            "model": self._model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You explain prediction market resolution rules in simple Russian. "
                        "Never provide buy/sell advice."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 220,
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("OpenAI resolution explanation failed: %s", exc)
            return None

        try:
            content = data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError, AttributeError):
            logger.warning("Unexpected OpenAI response shape for resolution")
            return None

        return content or None
