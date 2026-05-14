from __future__ import annotations

from datetime import datetime, timezone
import logging
import sys
from typing import Any


def setup_logging(level: str = "INFO") -> None:
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        stream=sys.stdout,
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("aiogram.event").setLevel(logging.INFO)


def log_callback_action(
    logger: logging.Logger,
    callback: Any,
    action: str,
    **fields: Any,
) -> None:
    telegram_user = getattr(callback, "from_user", None)
    log_user_action(logger, telegram_user, action, **fields)


def log_user_action(
    logger: logging.Logger,
    telegram_user: Any,
    action: str,
    **fields: Any,
) -> None:
    user_id = getattr(telegram_user, "id", None)
    username = getattr(telegram_user, "username", None) or "-"
    timestamp = datetime.now(timezone.utc).isoformat()
    extra_fields = " ".join(f"{key}={value}" for key, value in fields.items())
    suffix = f" {extra_fields}" if extra_fields else ""
    logger.info(
        "telegram_action timestamp=%s user_id=%s username=%s action=%s%s",
        timestamp,
        user_id,
        username,
        action,
        suffix,
    )
