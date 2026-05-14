from __future__ import annotations

from datetime import datetime

from bot.services.market_analyzer import MarketMovement
from bot.services.polymarket_client import Market


def format_probability(value: float | None) -> str:
    if value is None:
        return "данных пока нет"
    return f"{value * 100:.0f}%"


def format_percentage_points(value: float | None) -> str:
    if value is None:
        return "данных пока нет"
    return f"{value * 100:+.0f} п.п."


def format_usd(value: float | None) -> str:
    if value is None:
        return "данных пока нет"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"${value:,.0f}"
    return f"${value:.0f}"


def format_date(value: datetime | None) -> str:
    if value is None:
        return "данных пока нет"
    return value.date().isoformat()


def format_market_card(
    market: Market,
    explanation: str | None = None,
    heading: str = "🔥 Рынок:",
) -> str:
    lines = [
        heading,
        market.question,
        "",
        "Вероятность:",
        format_probability(market.yes_probability),
        "",
        "Объём:",
        format_usd(market.volume),
        "",
        "Завершение:",
        format_date(market.end_date),
    ]
    if explanation:
        lines.extend(["", "Короткое объяснение:", explanation])
    return "\n".join(lines)


def format_watchlist_card(title: str) -> str:
    return "\n".join(
        [
            "⭐ Watchlist:",
            title,
        ]
    )


def format_movement_card(
    movement: MarketMovement,
    explanation: str | None = None,
) -> str:
    direction = "выросла" if movement.delta > 0 else "снизилась"
    lines = [
        "⚡ Резкое движение:",
        movement.market.question,
        "",
        f"Вероятность {direction}:",
        f"{format_probability(movement.old_probability)} → {format_probability(movement.new_probability)}",
        "",
        "Изменение:",
        format_percentage_points(movement.delta),
        "",
        "Объём:",
        format_usd(movement.market.volume),
        "",
        "Завершение:",
        format_date(movement.market.end_date),
    ]
    if explanation:
        lines.extend(["", "Короткое объяснение:", explanation])
    return "\n".join(lines)
