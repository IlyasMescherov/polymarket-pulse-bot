from __future__ import annotations

import html
import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any
from xml.etree import ElementTree

import httpx

from bot.services.source_adapters.base import ExternalNewsItem, SourceConfig

logger = logging.getLogger(__name__)


DEFAULT_RSS_SOURCES: tuple[SourceConfig, ...] = (
    SourceConfig(
        source_type="rss",
        name="BBC World",
        url="https://feeds.bbci.co.uk/news/world/rss.xml",
        category="global",
        credibility_score=78,
    ),
    SourceConfig(
        source_type="rss",
        name="CNBC Top News",
        url="https://www.cnbc.com/id/100003114/device/rss/rss.html",
        category="global",
        credibility_score=74,
    ),
    SourceConfig(
        source_type="rss",
        name="CoinDesk",
        url="https://www.coindesk.com/arc/outboundfeeds/rss/",
        category="crypto",
        credibility_score=70,
    ),
    SourceConfig(
        source_type="rss",
        name="TechCrunch",
        url="https://techcrunch.com/feed/",
        category="ai",
        credibility_score=68,
    ),
    SourceConfig(
        source_type="rss",
        name="ESPN",
        url="https://www.espn.com/espn/rss/news",
        category="sports",
        credibility_score=72,
    ),
)


def _strip_html(value: str | None) -> str:
    if not value:
        return ""
    text = html.unescape(value)
    output: list[str] = []
    in_tag = False
    for char in text:
        if char == "<":
            in_tag = True
            continue
        if char == ">":
            in_tag = False
            continue
        if not in_tag:
            output.append(char)
    return " ".join("".join(output).split())


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError, IndexError):
        pass
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def _child_text(element: ElementTree.Element, *names: str) -> str:
    wanted = {name.lower() for name in names}
    for child in list(element):
        if _local_name(child.tag) in wanted:
            return _strip_html(child.text)
    return ""


def _link_text(element: ElementTree.Element) -> str:
    direct = _child_text(element, "link")
    if direct:
        return direct
    for child in list(element):
        if _local_name(child.tag) == "link":
            href = child.attrib.get("href")
            if href:
                return href.strip()
    return ""


def _entries(root: ElementTree.Element) -> list[ElementTree.Element]:
    rss_items = [element for element in root.iter() if _local_name(element.tag) == "item"]
    if rss_items:
        return rss_items
    return [element for element in root.iter() if _local_name(element.tag) == "entry"]


def _infer_urgency(title: str, summary: str) -> float:
    text = f"{title} {summary}".lower()
    score = 25.0
    urgent_terms = (
        "breaking",
        "court",
        "ruling",
        "deadline",
        "election",
        "ceasefire",
        "war",
        "fed",
        "sec",
        "bitcoin",
        "playoff",
        "final",
        "injury",
        "launch",
        "announcement",
    )
    score += sum(8.0 for term in urgent_terms if term in text)
    return min(95.0, score)


class RSSAdapter:
    def __init__(
        self,
        sources: tuple[SourceConfig, ...] | list[SourceConfig] = DEFAULT_RSS_SOURCES,
        *,
        timeout: float = 8.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._sources = tuple(source for source in sources if source.is_active)
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers={"User-Agent": "PulseMarketAI/1.0 (+https://pulsemarketai.com)"},
            follow_redirects=True,
        )

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def fetch(self, limit_per_source: int = 15) -> list[ExternalNewsItem]:
        items: list[ExternalNewsItem] = []
        for source in self._sources:
            try:
                response = await self._client.get(source.url)
                response.raise_for_status()
            except httpx.HTTPError as exc:
                logger.info("RSS source unavailable: %s (%s)", source.name, exc)
                continue
            items.extend(self.parse_feed(response.text, source, limit=limit_per_source))
        return items

    @staticmethod
    def parse_feed(
        xml_text: str,
        source: SourceConfig,
        *,
        limit: int = 15,
    ) -> list[ExternalNewsItem]:
        try:
            root = ElementTree.fromstring(xml_text)
        except ElementTree.ParseError:
            return []

        events: list[ExternalNewsItem] = []
        for entry in _entries(root)[:limit]:
            title = _child_text(entry, "title")
            url = _link_text(entry)
            if not title or not url:
                continue
            summary = _child_text(entry, "description", "summary", "content", "content:encoded")
            published = _child_text(entry, "pubDate", "published", "updated", "dc:date")
            events.append(
                ExternalNewsItem(
                    source_type=source.source_type,
                    source_name=source.name,
                    source_url=source.url,
                    title=title[:500],
                    summary=summary[:1000],
                    url=url,
                    published_at=_parse_datetime(published),
                    category=source.category,
                    urgency_score=_infer_urgency(title, summary),
                    credibility_score=source.credibility_score,
                    raw_payload={"feed_url": source.url},
                )
            )
        return events
