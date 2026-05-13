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


@dataclass(frozen=True, slots=True)
class Settings:
    bot_token: str
    database_url: str
    openai_api_key: str | None
    polymarket_base_url: str
    polymarket_builder_code: str | None
    project_public_url: str | None
    project_telegram_handle: str | None
    log_level: str
    app_host: str = "0.0.0.0"
    app_port: int = 8080
    market_poll_interval_seconds: int = 900
    movement_threshold: float = 0.10
    openai_model: str = "gpt-4o-mini"


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
        polymarket_builder_code=_optional(os.getenv("POLYMARKET_BUILDER_CODE")),
        project_public_url=_optional(os.getenv("PROJECT_PUBLIC_URL")),
        project_telegram_handle=_optional(os.getenv("PROJECT_TELEGRAM_HANDLE")),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        app_host=os.getenv("APP_HOST", "0.0.0.0"),
        app_port=int(os.getenv("APP_PORT", "8080")),
        market_poll_interval_seconds=int(
            os.getenv("MARKET_POLL_INTERVAL_SECONDS", "900")
        ),
        movement_threshold=float(os.getenv("MOVEMENT_THRESHOLD", "0.10")),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    )
