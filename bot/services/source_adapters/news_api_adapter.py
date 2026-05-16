from __future__ import annotations

from bot.services.source_adapters.base import ExternalNewsItem


class NewsAPIAdapter:
    """Optional API-backed news adapter.

    It stays as a no-op until an approved API key/provider is configured.
    """

    def __init__(self, api_key: str | None = None, *, enabled: bool = False) -> None:
        self.api_key = api_key
        self.enabled = enabled and bool(api_key)

    async def fetch(self, limit_per_source: int = 20) -> list[ExternalNewsItem]:
        return []
