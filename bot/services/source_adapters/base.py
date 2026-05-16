from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class SourceConfig:
    source_type: str
    name: str
    url: str
    category: str = "global"
    credibility_score: float = 60.0
    is_active: bool = True


@dataclass(frozen=True, slots=True)
class ExternalNewsItem:
    source_type: str
    source_name: str
    source_url: str
    title: str
    summary: str
    url: str
    published_at: datetime | None = None
    category: str = "global"
    entities: tuple[str, ...] = ()
    topics: tuple[str, ...] = ()
    sentiment: str | None = None
    urgency_score: float = 0.0
    credibility_score: float = 0.0
    raw_payload: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_type": self.source_type,
            "source_name": self.source_name,
            "source_url": self.source_url,
            "title": self.title,
            "summary": self.summary,
            "url": self.url,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "category": self.category,
            "entities": list(self.entities),
            "topics": list(self.topics),
            "sentiment": self.sentiment,
            "urgency_score": self.urgency_score,
            "credibility_score": self.credibility_score,
            "raw_payload": dict(self.raw_payload),
        }
