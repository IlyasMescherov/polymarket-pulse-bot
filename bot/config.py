from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _optional(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _database_url(value: str | None) -> str:
    url = value or "postgresql+asyncpg://pulse:pulse@localhost:5432/pulsemarket"
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


def _int_set(value: str | None) -> frozenset[int]:
    if not value:
        return frozenset()
    ids: set[int] = set()
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            ids.add(int(item))
        except ValueError:
            continue
    return frozenset(ids)


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _telegram_channel_id(value: str | None) -> str | None:
    normalized = _optional(value)
    if normalized is None:
        return None
    for prefix in ("https://t.me/", "http://t.me/", "t.me/"):
        if normalized.startswith(prefix):
            handle = normalized.removeprefix(prefix).strip("/")
            return f"@{handle}" if handle and not handle.startswith("@") else handle
    return normalized


@dataclass(frozen=True, slots=True)
class Settings:
    bot_token: str
    database_url: str
    openai_api_key: str | None
    polymarket_base_url: str
    polymarket_data_api_url: str
    polymarket_builder_code: str | None
    polymarket_referral_url: str | None
    project_public_url: str | None
    project_telegram_handle: str | None
    project_channel_url: str | None
    project_support_url: str | None
    project_x_url: str | None
    mini_app_url: str | None
    project_channel_id: str | None
    admin_telegram_ids: frozenset[int]
    log_level: str
    app_host: str = "0.0.0.0"
    app_port: int = 8080
    market_poll_interval_seconds: int = 900
    movement_threshold: float = 0.10
    smart_money_active_market_min_usd: float = 1000.0
    auto_channel_posting_enabled: bool = False
    auto_channel_posting_time: str = "09:00"
    auto_channel_posting_timezone: str = "UTC"
    auto_channel_posting_min_hours_between_posts: int = 20
    x_drafts_enabled: bool = True
    x_posting_mode: str = "draft"
    x_handle: str | None = None
    auto_x_posting_enabled: bool = False
    x_api_key: str | None = None
    x_api_secret: str | None = None
    x_access_token: str | None = None
    x_access_token_secret: str | None = None
    openai_model: str = "gpt-4o-mini"
    news_refresh_minutes: int = 10
    enable_x_source: bool = False
    enable_telegram_source: bool = False
    enable_rss_source: bool = True
    enable_official_sources: bool = True


@lru_cache(maxsize=1)
def load_settings() -> Settings:
    load_dotenv(PROJECT_ROOT / ".env")

    return Settings(
        bot_token=os.getenv("BOT_TOKEN", "").strip(),
        database_url=_database_url(os.getenv("DATABASE_URL")),
        openai_api_key=_optional(os.getenv("OPENAI_API_KEY")),
        polymarket_base_url=os.getenv(
            "POLYMARKET_BASE_URL",
            "https://gamma-api.polymarket.com",
        ).rstrip("/"),
        polymarket_data_api_url=os.getenv(
            "POLYMARKET_DATA_API_URL",
            "https://data-api.polymarket.com",
        ).rstrip("/"),
        polymarket_builder_code=_optional(os.getenv("POLYMARKET_BUILDER_CODE")),
        polymarket_referral_url=_optional(os.getenv("POLYMARKET_REFERRAL_URL")),
        project_public_url=_optional(os.getenv("PROJECT_PUBLIC_URL")),
        project_telegram_handle=_optional(os.getenv("PROJECT_TELEGRAM_HANDLE")),
        project_channel_url=_optional(os.getenv("PROJECT_CHANNEL_URL")),
        project_support_url=_optional(os.getenv("PROJECT_SUPPORT_URL")),
        project_x_url=_optional(os.getenv("PROJECT_X_URL"))
        or _optional(os.getenv("PROJECT_TWITTER_URL")),
        mini_app_url=_optional(os.getenv("MINI_APP_URL")),
        project_channel_id=_telegram_channel_id(os.getenv("PROJECT_CHANNEL_ID"))
        or _telegram_channel_id(os.getenv("PROJECT_CHANNEL_URL")),
        admin_telegram_ids=_int_set(os.getenv("ADMIN_TELEGRAM_IDS")),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        app_host=os.getenv("APP_HOST", "0.0.0.0"),
        app_port=int(os.getenv("APP_PORT", "8080")),
        market_poll_interval_seconds=int(
            os.getenv("MARKET_POLL_INTERVAL_SECONDS", "900")
        ),
        movement_threshold=float(os.getenv("MOVEMENT_THRESHOLD", "0.10")),
        smart_money_active_market_min_usd=float(
            os.getenv("SMART_MONEY_ACTIVE_MARKET_MIN_USD", "1000")
        ),
        auto_channel_posting_enabled=_bool(
            os.getenv("AUTO_CHANNEL_POSTING_ENABLED"),
            default=False,
        ),
        auto_channel_posting_time=os.getenv("AUTO_CHANNEL_POSTING_TIME", "09:00"),
        auto_channel_posting_timezone=os.getenv(
            "AUTO_CHANNEL_POSTING_TIMEZONE",
            "UTC",
        ),
        auto_channel_posting_min_hours_between_posts=int(
            os.getenv("AUTO_CHANNEL_POSTING_MIN_HOURS_BETWEEN_POSTS", "20")
        ),
        x_drafts_enabled=_bool(os.getenv("X_DRAFTS_ENABLED"), default=True),
        x_posting_mode=os.getenv("X_POSTING_MODE", "draft").strip().lower() or "draft",
        x_handle=_optional(os.getenv("X_HANDLE")),
        auto_x_posting_enabled=_bool(os.getenv("AUTO_X_POSTING_ENABLED"), default=False),
        x_api_key=_optional(os.getenv("X_API_KEY")),
        x_api_secret=_optional(os.getenv("X_API_SECRET")),
        x_access_token=_optional(os.getenv("X_ACCESS_TOKEN")),
        x_access_token_secret=_optional(os.getenv("X_ACCESS_TOKEN_SECRET")),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        news_refresh_minutes=int(os.getenv("NEWS_REFRESH_MINUTES", "10")),
        enable_x_source=_bool(os.getenv("ENABLE_X_SOURCE"), default=False),
        enable_telegram_source=_bool(os.getenv("ENABLE_TELEGRAM_SOURCE"), default=False),
        enable_rss_source=_bool(os.getenv("ENABLE_RSS_SOURCE"), default=True),
        enable_official_sources=_bool(
            os.getenv("ENABLE_OFFICIAL_SOURCES"),
            default=True,
        ),
    )
