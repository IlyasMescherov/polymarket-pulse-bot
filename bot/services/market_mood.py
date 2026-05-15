from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from bot.services.polymarket_client import Market
from bot.utils.i18n import normalize_language


@dataclass(frozen=True, slots=True)
class MarketMood:
    key: str
    label: str
    reason: str


def _seconds_until(end_date: datetime | None, now: datetime | None = None) -> float | None:
    if end_date is None:
        return None
    current = now or datetime.now(timezone.utc)
    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=timezone.utc)
    return (end_date - current).total_seconds()


def market_mood_key(
    market: Market,
    delta: float | None = None,
    now: datetime | None = None,
) -> str:
    seconds_left = _seconds_until(market.end_date, now=now)
    if seconds_left is not None and seconds_left <= 24 * 60 * 60:
        return "ending_soon"

    abs_delta = abs(delta or 0)
    if abs_delta >= 0.10:
        return "volatile"
    if abs_delta >= 0.05 or (market.volume or 0) >= 500_000:
        return "heating_up"
    if (market.volume or 0) >= 100_000:
        return "active"
    return "quiet"


def market_mood_label(key: str, language: str | None = None) -> str:
    normalized = normalize_language(language)
    labels = {
        "en": {
            "quiet": "Quiet",
            "active": "Active",
            "heating_up": "Heating up",
            "volatile": "Volatile",
            "ending_soon": "Ending soon",
        },
        "ru": {
            "quiet": "Тихо",
            "active": "Активно",
            "heating_up": "Разогревается",
            "volatile": "Волатильно",
            "ending_soon": "Скоро завершение",
        },
    }
    return labels[normalized].get(key, labels[normalized]["quiet"])


def market_mood_reason(key: str, language: str | None = None) -> str:
    normalized = normalize_language(language)
    reasons = {
        "en": {
            "quiet": "No strong movement yet.",
            "active": "Public attention is present.",
            "heating_up": "Attention is rising around this market.",
            "volatile": "Probability moved enough to make the market noticeable.",
            "ending_soon": "The market is close to resolution.",
        },
        "ru": {
            "quiet": "Сильного движения пока нет.",
            "active": "Публичное внимание уже есть.",
            "heating_up": "Внимание к этому рынку растёт.",
            "volatile": "Вероятность заметно изменилась, поэтому рынок выделяется.",
            "ending_soon": "Рынок близок к разрешению.",
        },
    }
    return reasons[normalized].get(key, reasons[normalized]["quiet"])


def calculate_market_mood(
    market: Market,
    delta: float | None = None,
    language: str | None = None,
    now: datetime | None = None,
) -> MarketMood:
    key = market_mood_key(market, delta=delta, now=now)
    return MarketMood(
        key=key,
        label=market_mood_label(key, language),
        reason=market_mood_reason(key, language),
    )
