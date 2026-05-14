from __future__ import annotations

from datetime import datetime, timezone

from bot.database.models import MarketSnapshot, UserWatchlist
from bot.services.market_analyzer import MarketMovement
from bot.services.polymarket_client import Market
from bot.services.pulse_score import PulseScore


def format_probability(value: float | None) -> str:
    if value is None:
        return "данных пока нет"
    return f"{value * 100:.0f}%"


def format_percentage_points(value: float | None) -> str:
    if value is None:
        return "данных пока нет"
    return f"{value * 100:+.0f}%"


def format_usd(value: float | None) -> str:
    if value is None:
        return "данных пока нет"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"${value:,.0f}"
    return f"${value:.0f}"


def format_compact_usd(value: float | None) -> str:
    if value is None:
        return "данных пока нет"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"${value / 1_000:.0f}K"
    return f"${value:.0f}"


def format_date(value: datetime | None) -> str:
    if value is None:
        return "данных пока нет"
    return value.date().isoformat()


def format_time_until(value: datetime | None, now: datetime | None = None) -> str:
    if value is None:
        return "данных пока нет"
    current = now or datetime.now(timezone.utc)
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    seconds = int((value - current).total_seconds())
    if seconds <= 0:
        return "завершён или скоро завершится"
    days = seconds // 86_400
    if days >= 1:
        return f"{days} days"
    hours = max(1, seconds // 3_600)
    return f"{hours} hours"


def format_market_card(
    market: Market,
    explanation: str | None = None,
    heading: str = "🔥 Горячий рынок",
    movement_delta: float | None = None,
    pulse_score: PulseScore | None = None,
    risk_flags: list[str] | None = None,
) -> str:
    lines = [
        heading,
        "",
        "Название:",
        market.question,
        "",
        "Вероятность:",
        format_probability(market.yes_probability),
        "",
        "Движение:",
        f"{format_percentage_points(movement_delta)} за 24ч"
        if movement_delta is not None
        else "данных пока нет",
        "",
        "Объём:",
        format_compact_usd(market.volume),
        "",
        "До завершения:",
        format_time_until(market.end_date),
    ]
    if pulse_score is not None:
        lines.extend(
            [
                "",
                "⚡ Pulse Score:",
                f"{pulse_score.value}/100 · {pulse_score.label}",
            ]
        )
    if risk_flags:
        lines.extend(["", "Риски:", *risk_flags[:3]])
    if explanation:
        lines.extend(["", "AI brief:", explanation])
    return "\n".join(lines)


def format_watchlist_card(item: UserWatchlist) -> str:
    delta = None
    if item.initial_probability is not None and item.last_probability is not None:
        delta = item.last_probability - item.initial_probability
    return "\n".join(
        [
            "⭐ Watchlist",
            "",
            "Название:",
            item.market_title,
            "",
            "Было:",
            format_probability(item.initial_probability),
            "",
            "Сейчас:",
            format_probability(item.last_probability),
            "",
            "Изменение:",
            format_percentage_points(delta),
        ]
    )


def format_movement_card(
    movement: MarketMovement,
    explanation: str | None = None,
    pulse_score: PulseScore | None = None,
    risk_flags: list[str] | None = None,
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
        format_compact_usd(movement.market.volume),
        "",
        "До завершения:",
        format_time_until(movement.market.end_date),
    ]
    if pulse_score is not None:
        lines.extend(["", "⚡ Pulse Score:", f"{pulse_score.value}/100 · {pulse_score.label}"])
    if risk_flags:
        lines.extend(["", "Риски:", *risk_flags[:3]])
    if explanation:
        lines.extend(["", "AI brief:", explanation])
    return "\n".join(lines)


def format_market_timeline(snapshots: list[MarketSnapshot]) -> str:
    if len(snapshots) < 3:
        return (
            "📊 Динамика рынка\n\n"
            "Пока мало данных. Бот начнёт показывать динамику после нескольких обновлений."
        )

    values = [snapshot.yes_probability for snapshot in snapshots if snapshot.yes_probability is not None]
    if len(values) < 3:
        return (
            "📊 Динамика рынка\n\n"
            "Пока мало данных. Бот начнёт показывать динамику после нескольких обновлений."
        )

    delta = values[-1] - values[0]
    chain = " → ".join(format_probability(value) for value in values[-8:])
    return "\n".join(
        [
            "📊 Динамика рынка",
            "",
            "24ч:",
            chain,
            "",
            "Изменение:",
            format_percentage_points(delta),
            "",
            "Снимков:",
            str(len(values)),
        ]
    )


def format_beginner_explanation(market: Market, ai_brief: str | None = None) -> str:
    lines = [
        "🧠 Объяснить проще",
        "",
        "Этот рынок показывает, насколько участники Polymarket верят в событие.",
        "",
        f"{format_probability(market.yes_probability)} означает, что рынок сейчас оценивает событие примерно так.",
        "",
        "Это не гарантия.",
        "Это мнение рынка на данный момент.",
        "",
        "Обрати внимание:",
        "• объём",
        "• дату завершения",
        "• резкие движения",
        "• правила разрешения рынка",
    ]
    if ai_brief:
        lines.extend(["", "AI brief:", ai_brief])
    return "\n".join(lines)


def format_share_market_card(market: Market, pulse_score: PulseScore | None = None) -> str:
    lines = [
        "📤 Рынок Polymarket",
        "",
        market.question,
        "",
        f"Вероятность: {format_probability(market.yes_probability)}",
        f"Объём: {format_compact_usd(market.volume)}",
    ]
    if pulse_score is not None:
        lines.append(f"Pulse Score: {pulse_score.value}/100 · {pulse_score.label}")
    lines.extend(
        [
            "",
            "PulseMarket AI показывает горячие рынки, резкие движения и объясняет всё простым языком.",
            market.url,
        ]
    )
    return "\n".join(lines)
