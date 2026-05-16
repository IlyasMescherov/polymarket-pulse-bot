from __future__ import annotations

from bot.services.source_adapters.base import ExternalNewsItem


class XAdapter:
    """Approved-provider placeholder for public X posts.

    The MVP keeps this disabled unless a safe API/provider is configured.
    """

    def __init__(self, *, enabled: bool = False) -> None:
        self.enabled = enabled

    async def fetch(self, limit_per_source: int = 20) -> list[ExternalNewsItem]:
        return []
