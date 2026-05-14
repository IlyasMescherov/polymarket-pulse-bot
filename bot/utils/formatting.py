from __future__ import annotations

from datetime import datetime, timezone

from bot.database.models import MarketSnapshot, UserWatchlist
from bot.services.market_analyzer import MarketMovement
from bot.services.market_health import MarketHealth
from bot.services.polymarket_client import Market
from bot.services.pulse_score import PulseScore
from bot.utils.i18n import normalize_language


def _missing_data(language: str | None = None) -> str:
    return "data not available yet" if normalize_language(language) == "en" else "данных пока нет"


def _label(ru: str, en: str, language: str | None = None) -> str:
    return en if normalize_language(language) == "en" else ru


def format_probability(value: float | None, language: str | None = None) -> str:
    if value is None:
        return _missing_data(language)
    return f"{value * 100:.0f}%"


def format_percentage_points(value: float | None, language: str | None = None) -> str:
    if value is None:
        return _missing_data(language)
    return f"{value * 100:+.0f}%"


def format_usd(value: float | None) -> str:
    if value is None:
        return "данных пока нет"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"${value:,.0f}"
    return f"${value:.0f}"


def format_compact_usd(value: float | None, language: str | None = None) -> str:
    if value is None:
        return _missing_data(language)
    if value >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"${value / 1_000:.0f}K"
    return f"${value:.0f}"


def format_date(value: datetime | None, language: str | None = None) -> str:
    if value is None:
        return _missing_data(language)
    return value.date().isoformat()


def format_time_until(
    value: datetime | None,
    now: datetime | None = None,
    language: str | None = None,
) -> str:
    if value is None:
        return _missing_data(language)
    current = now or datetime.now(timezone.utc)
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    seconds = int((value - current).total_seconds())
    if seconds <= 0:
        return _label("завершён или скоро завершится", "ended or ending soon", language)
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
    market_health: MarketHealth | None = None,
    risk_flags: list[str] | None = None,
    language: str | None = None,
) -> str:
    lines = [
        heading,
        "",
        _label("Название:", "Title:", language),
        market.question,
        "",
        _label("Вероятность:", "Probability:", language),
        format_probability(market.yes_probability, language),
        "",
        _label("Движение:", "Movement:", language),
        (
            f"{format_percentage_points(movement_delta, language)} "
            f"{_label('за 24ч', 'over 24h', language)}"
        )
        if movement_delta is not None
        else _missing_data(language),
        "",
        _label("Объём:", "Volume:", language),
        format_compact_usd(market.volume, language),
        "",
        _label("До завершения:", "Time left:", language),
        format_time_until(market.end_date, language=language),
    ]
    if pulse_score is not None:
        lines.extend(
            [
                "",
                "⚡ Pulse Score:",
                f"{pulse_score.value}/100 · {pulse_score.label}",
            ]
        )
    if market_health is not None:
        lines.extend(
            [
                "",
                "🩺 Market Health:",
                f"{market_health.value}/100 · {market_health.label}",
            ]
        )
    if risk_flags:
        lines.extend(["", _label("Риски:", "Risk flags:", language), *risk_flags[:3]])
    if explanation:
        lines.extend(["", "AI brief:", explanation])
    return "\n".join(lines)


def format_watchlist_card(item: UserWatchlist, language: str | None = None) -> str:
    delta = None
    if item.initial_probability is not None and item.last_probability is not None:
        delta = item.last_probability - item.initial_probability
    return "\n".join(
        [
            "⭐ Watchlist",
            "",
            _label("Название:", "Title:", language),
            item.market_title,
            "",
            _label("Было:", "Initial:", language),
            format_probability(item.initial_probability, language),
            "",
            _label("Сейчас:", "Current:", language),
            format_probability(item.last_probability, language),
            "",
            _label("Изменение:", "Change:", language),
            format_percentage_points(delta, language),
        ]
    )


def format_movement_card(
    movement: MarketMovement,
    explanation: str | None = None,
    pulse_score: PulseScore | None = None,
    market_health: MarketHealth | None = None,
    risk_flags: list[str] | None = None,
    language: str | None = None,
) -> str:
    if normalize_language(language) == "en":
        direction = "increased" if movement.delta > 0 else "decreased"
        movement_label = f"Probability {direction}:"
    else:
        direction = "выросла" if movement.delta > 0 else "снизилась"
        movement_label = f"Вероятность {direction}:"
    lines = [
        _label("⚡ Резкое движение:", "⚡ Sharp move:", language),
        movement.market.question,
        "",
        movement_label,
        f"{format_probability(movement.old_probability, language)} → {format_probability(movement.new_probability, language)}",
        "",
        _label("Изменение:", "Change:", language),
        format_percentage_points(movement.delta, language),
        "",
        _label("Объём:", "Volume:", language),
        format_compact_usd(movement.market.volume, language),
        "",
        _label("До завершения:", "Time left:", language),
        format_time_until(movement.market.end_date, language=language),
    ]
    if pulse_score is not None:
        lines.extend(["", "⚡ Pulse Score:", f"{pulse_score.value}/100 · {pulse_score.label}"])
    if market_health is not None:
        lines.extend(["", "🩺 Market Health:", f"{market_health.value}/100 · {market_health.label}"])
    if risk_flags:
        lines.extend(["", _label("Риски:", "Risk flags:", language), *risk_flags[:3]])
    if explanation:
        lines.extend(["", "AI brief:", explanation])
    return "\n".join(lines)


def format_market_timeline(
    snapshots: list[MarketSnapshot],
    language: str | None = None,
) -> str:
    if len(snapshots) < 3:
        if normalize_language(language) == "en":
            return (
                "📊 Market timeline\n\n"
                "Not enough data yet. The bot will show a timeline after a few updates."
            )
        return "📊 Динамика рынка\n\nПока мало данных. Бот начнёт показывать динамику после нескольких обновлений."

    values = [snapshot.yes_probability for snapshot in snapshots if snapshot.yes_probability is not None]
    if len(values) < 3:
        if normalize_language(language) == "en":
            return (
                "📊 Market timeline\n\n"
                "Not enough data yet. The bot will show a timeline after a few updates."
            )
        return "📊 Динамика рынка\n\nПока мало данных. Бот начнёт показывать динамику после нескольких обновлений."

    delta = values[-1] - values[0]
    chain = " → ".join(format_probability(value, language) for value in values[-8:])
    return "\n".join(
        [
            _label("📊 Динамика рынка", "📊 Market timeline", language),
            "",
            "24ч:",
            chain,
            "",
            _label("Изменение:", "Change:", language),
            format_percentage_points(delta, language),
            "",
            _label("Снимков:", "Snapshots:", language),
            str(len(values)),
        ]
    )


def format_beginner_explanation(
    market: Market,
    ai_brief: str | None = None,
    language: str | None = None,
) -> str:
    if normalize_language(language) == "en":
        lines = [
            "🧠 Simple explanation",
            "",
            "This market shows how strongly Polymarket participants believe an event may happen.",
            "",
            f"{format_probability(market.yes_probability, language)} is the market's current estimate.",
            "",
            "It is not a guarantee.",
            "It is the market's opinion at this moment.",
            "",
            "Watch:",
            "• volume",
            "• end date",
            "• sharp moves",
            "• resolution rules",
        ]
        if ai_brief:
            lines.extend(["", "AI brief:", ai_brief])
        return "\n".join(lines)

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


def format_share_market_card(
    market: Market,
    pulse_score: PulseScore | None = None,
    language: str | None = None,
) -> str:
    if normalize_language(language) == "en":
        lines = [
            "📤 Polymarket market",
            "",
            market.question,
            "",
            f"Probability: {format_probability(market.yes_probability, language)}",
            f"Volume: {format_compact_usd(market.volume, language)}",
        ]
        if pulse_score is not None:
            lines.append(f"Pulse Score: {pulse_score.value}/100 · {pulse_score.label}")
        lines.extend(
            [
                "",
                "PulseMarket AI shows hot markets, sharp moves, and plain-language explanations.",
                market.url,
            ]
        )
        return "\n".join(lines)

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
