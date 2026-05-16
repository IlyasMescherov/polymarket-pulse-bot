from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable

from bot.services.polymarket_client import Market
from bot.utils.i18n import normalize_language


@dataclass(frozen=True, slots=True)
class EventCategory:
    key: str
    en_label: str
    ru_label: str
    keywords: tuple[str, ...]


EVENT_CATEGORIES: tuple[EventCategory, ...] = (
    EventCategory(
        key="politics",
        en_label="Politics",
        ru_label="Политика",
        keywords=(
            "trump",
            "election",
            "president",
            "senate",
            "congress",
            "biden",
            "iran",
            "israel",
            "china",
            "russia",
            "ukraine",
            "war",
            "diplomacy",
            "minister",
            "government",
        ),
    ),
    EventCategory(
        key="crypto",
        en_label="Crypto",
        ru_label="Крипто",
        keywords=(
            "bitcoin",
            "btc",
            "ethereum",
            "eth",
            "solana",
            "xrp",
            "crypto",
            "binance",
            "coinbase",
            "stablecoin",
        ),
    ),
    EventCategory(
        key="ai",
        en_label="AI",
        ru_label="AI",
        keywords=(
            "ai",
            "openai",
            "nvidia",
            "tesla",
            "apple",
            "google",
            "microsoft",
            "anthropic",
            "model",
            "robot",
        ),
    ),
    EventCategory(
        key="sports",
        en_label="Sports",
        ru_label="Спорт",
        keywords=(
            "nba",
            "nfl",
            "ufc",
            "soccer",
            "football",
            "tennis",
            "baseball",
            "fifa",
            "playoff",
            "championship",
        ),
    ),
    EventCategory(
        key="esports",
        en_label="Esports",
        ru_label="Киберспорт",
        keywords=("cs2", "csgo", "dota", "valorant", "lol", "league of legends", "esports"),
    ),
    EventCategory(
        key="global",
        en_label="Global",
        ru_label="Мировые",
        keywords=(
            "fed",
            "inflation",
            "rates",
            "recession",
            "cpi",
            "jobs",
            "gdp",
            "earthquake",
            "climate",
            "global",
        ),
    ),
    EventCategory(
        key="culture",
        en_label="Culture",
        ru_label="Культура",
        keywords=(
            "oscars",
            "grammy",
            "movie",
            "film",
            "music",
            "celebrity",
            "youtube",
            "twitter",
            "x.com",
        ),
    ),
)

DEFAULT_CATEGORY_KEY = "all"


def category_label(key: str | None, language: str | None = None) -> str:
    normalized = normalize_language(language)
    if key == DEFAULT_CATEGORY_KEY or not key:
        return "All" if normalized == "en" else "Все"
    for category in EVENT_CATEGORIES:
        if category.key == key:
            return category.en_label if normalized == "en" else category.ru_label
    return "Other" if normalized == "en" else "Другое"


def category_options(language: str | None = None) -> list[dict[str, str]]:
    return [
        {"key": DEFAULT_CATEGORY_KEY, "label": category_label(DEFAULT_CATEGORY_KEY, language)},
        *[
            {
                "key": category.key,
                "label": category.en_label
                if normalize_language(language) == "en"
                else category.ru_label,
            }
            for category in EVENT_CATEGORIES
        ],
    ]


def _market_text(market: Market) -> str:
    tags: list[str] = []
    raw_tags = market.raw.get("tags")
    if isinstance(raw_tags, list):
        for tag in raw_tags:
            if isinstance(tag, dict):
                tags.append(str(tag.get("label") or tag.get("name") or ""))
            else:
                tags.append(str(tag))
    return " ".join(
        [
            market.question,
            str(market.raw.get("description") or ""),
            str(market.raw.get("category") or ""),
            " ".join(tags),
        ]
    ).lower()


def classify_market_category(market: Market) -> str:
    text = _market_text(market)
    scores: dict[str, int] = {}
    for category in EVENT_CATEGORIES:
        score = sum(1 for keyword in category.keywords if _contains_keyword(text, keyword))
        if score:
            scores[category.key] = score
    if not scores:
        return "global"
    return max(scores.items(), key=lambda item: item[1])[0]


def _contains_keyword(text: str, keyword: str) -> bool:
    normalized = str(keyword).lower().strip()
    if not normalized:
        return False
    if "." in normalized or " " in normalized:
        return normalized in text
    return re.search(rf"(?<![a-z0-9]){re.escape(normalized)}(?![a-z0-9])", text) is not None


def filter_markets_by_category(markets: Iterable[Market], category_key: str | None) -> list[Market]:
    if not category_key or category_key == DEFAULT_CATEGORY_KEY:
        return list(markets)
    return [market for market in markets if classify_market_category(market) == category_key]
