from __future__ import annotations

from bot.services.source_adapters.base import ExternalNewsItem, SourceConfig
from bot.services.source_adapters.rss_adapter import RSSAdapter


OFFICIAL_RSS_SOURCES: tuple[SourceConfig, ...] = (
    SourceConfig(
        source_type="official",
        name="White House Briefing Room",
        url="https://www.whitehouse.gov/briefing-room/feed/",
        category="politics",
        credibility_score=94,
    ),
    SourceConfig(
        source_type="official",
        name="Federal Reserve",
        url="https://www.federalreserve.gov/feeds/press_all.xml",
        category="economy",
        credibility_score=94,
    ),
    SourceConfig(
        source_type="official",
        name="SEC Press Releases",
        url="https://www.sec.gov/news/pressreleases.rss",
        category="crypto",
        credibility_score=92,
    ),
    SourceConfig(
        source_type="official",
        name="OpenAI News",
        url="https://openai.com/news/rss.xml",
        category="ai",
        credibility_score=90,
    ),
)


class OfficialSourcesAdapter:
    """Public official RSS feeds only. No private sources or paywall bypassing."""

    def __init__(
        self,
        sources: tuple[SourceConfig, ...] | list[SourceConfig] = OFFICIAL_RSS_SOURCES,
        *,
        timeout: float = 8.0,
    ) -> None:
        self._rss = RSSAdapter(sources, timeout=timeout)

    async def close(self) -> None:
        await self._rss.close()

    async def fetch(self, limit_per_source: int = 10) -> list[ExternalNewsItem]:
        return await self._rss.fetch(limit_per_source=limit_per_source)
