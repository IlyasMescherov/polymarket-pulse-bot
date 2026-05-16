from __future__ import annotations

from bot.services.source_adapters.base import ExternalNewsItem


class TelegramPublicAdapter:
    """Placeholder for public Telegram channels.

    This adapter intentionally does not scrape private chats or closed sources.
    """

    def __init__(self, *, enabled: bool = False) -> None:
        self.enabled = enabled

    async def fetch(self, limit_per_source: int = 20) -> list[ExternalNewsItem]:
        return []
